import datetime

from decimal import Decimal

from multicallable import Multicallable
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models import (
    BalanceChange,
    BalanceChangeType,
    BinanceIncome,
    HedgerSnapshot,
    Quote,
    StatsBotMessage,
    RuntimeConfiguration,
)
from config.settings import (
    Context,
    SYMMIO_ABI,
    HedgerContext,
    IGNORE_BINANCE_TRADE_VOLUME,
)
from cronjobs.binance_trade_volume import calculate_binance_trade_volume
from cronjobs.snapshot.snapshot_context import SnapshotContext
from services.binance_service import real_time_funding_rate
from services.snaphshot_service import get_last_affiliate_snapshot_for
from utils.attr_dict import AttrDict
from utils.block import Block
from utils.gas_checker import gas_used_by_hedger_wallets


def prepare_hedger_snapshot(
    snapshot_context: SnapshotContext,
    hedger_context: HedgerContext,
    block: Block,
):
    print(f"----------------Prepare Hedger Snapshot Of {hedger_context.name}")
    context: Context = snapshot_context.context
    session: Session = snapshot_context.session
    config: RuntimeConfiguration = snapshot_context.config

    has_binance_data = hedger_context.utils.binance_client is not None

    snapshot = AttrDict()

    snapshot.gas, snapshot.gas_dollar = gas_used_by_hedger_wallets(snapshot_context, hedger_context)

    print(f"Total gas spent by all wallets of {hedger_context.name}: {snapshot.gas} (${snapshot.gas_dollar})")

    if has_binance_data:
        transfer_sum = session.execute(
            select(func.coalesce(func.sum(BinanceIncome.amount), 0)).where(
                and_(
                    BinanceIncome.timestamp <= block.datetime(),
                    BinanceIncome.type == "TRANSFER",
                    BinanceIncome.tenant == context.tenant,
                    BinanceIncome.hedger == hedger_context.name,
                )
            )
        ).scalar_one()

        internal_transfer_sum = session.execute(
            select(func.coalesce(func.sum(BinanceIncome.amount), 0)).where(
                and_(
                    BinanceIncome.timestamp <= block.datetime(),
                    BinanceIncome.type == "INTERNAL_TRANSFER",
                    BinanceIncome.tenant == context.tenant,
                    BinanceIncome.hedger == hedger_context.name,
                )
            )
        ).scalar_one()

        total_transfers = transfer_sum + internal_transfer_sum

        is_negative = total_transfers < 0
        snapshot.binance_deposit = (
            Decimal(-(abs(total_transfers) * 10**18) if is_negative else total_transfers * 10**18) + hedger_context.binance_deposit_diff
        )

        if not block.is_for_past():
            binance_account = hedger_context.utils.binance_client.futures_account(version=2)
            snapshot.binance_maintenance_margin = Decimal(float(binance_account["totalMaintMargin"]) * 10**18)
            snapshot.binance_total_balance = Decimal(float(binance_account["totalMarginBalance"]) * 10**18)
            snapshot.binance_account_health_ratio = 100 - (snapshot.binance_maintenance_margin / snapshot.binance_total_balance) * 100
            snapshot.binance_cross_upnl = Decimal(binance_account["totalCrossUnPnl"]) * 10**18
            snapshot.binance_av_balance = Decimal(binance_account["availableBalance"]) * 10**18
            snapshot.binance_total_initial_margin = Decimal(binance_account["totalInitialMargin"]) * 10**18
            snapshot.binance_max_withdraw_amount = Decimal(binance_account["maxWithdrawAmount"]) * 10**18
            snapshot.max_open_interest = Decimal(hedger_context.hedger_max_open_interest_ratio * snapshot.binance_max_withdraw_amount)
        else:
            stat_message = session.scalar(
                select(StatsBotMessage).where(
                    and_(
                        StatsBotMessage.timestamp <= block.datetime(),
                        StatsBotMessage.timestamp >= block.datetime() - datetime.timedelta(minutes=3),
                        StatsBotMessage.tenant == context.tenant,
                    )
                )
            )
            if not stat_message:
                raise Exception(f"{context.tenant}: StatBot message not found for date: {block.datetime()}")

            snapshot.binance_maintenance_margin = stat_message.content["Total Maint. Margin"]
            snapshot.binance_total_balance = stat_message.content["Total Margin Balance"]
            snapshot.binance_account_health_ratio = stat_message.content["Health Ratio"]
            snapshot.binance_cross_upnl = stat_message.content["Total Cross UnPnl"]
            snapshot.binance_av_balance = stat_message.content["Available Balance"]
            snapshot.binance_total_initial_margin = stat_message.content["Total Initial Margin"]
            snapshot.binance_max_withdraw_amount = stat_message.content["Max Withdraw Amount"]
            snapshot.max_open_interest = Decimal(hedger_context.hedger_max_open_interest_ratio * snapshot.binance_max_withdraw_amount)

        snapshot.binance_trade_volume = (
            0 if IGNORE_BINANCE_TRADE_VOLUME else Decimal(calculate_binance_trade_volume(context, session, hedger_context, block) * 10**18)
        )

        # ------------------------------------------
        snapshot.binance_paid_funding_fee = session.execute(
            select(func.coalesce(func.sum(BinanceIncome.amount), Decimal(0))).where(
                and_(
                    BinanceIncome.timestamp <= block.datetime(),
                    BinanceIncome.amount < 0,
                    BinanceIncome.type == "FUNDING_FEE",
                    BinanceIncome.tenant == context.tenant,
                )
            )
        ).scalar_one()

        snapshot.binance_received_funding_fee = session.execute(
            select(func.coalesce(func.sum(BinanceIncome.amount), Decimal(0))).where(
                and_(
                    BinanceIncome.timestamp <= block.datetime(),
                    BinanceIncome.amount > 0,
                    BinanceIncome.type == "FUNDING_FEE",
                    BinanceIncome.tenant == context.tenant,
                )
            )
        ).scalar_one()

        if not block.is_for_past():
            positions = hedger_context.utils.binance_client.futures_position_information()
            open_positions = [p for p in positions if Decimal(p["notional"]) != 0]
            binance_next_funding_fee = 0
            for pos in open_positions:
                notional, symbol, _ = (
                    Decimal(pos["notional"]),
                    pos["symbol"],
                    pos["positionSide"],
                )
                funding_rate = pos["fundingRate"] = real_time_funding_rate(symbol=symbol)
                funding_rate_fee = -1 * notional * funding_rate
                binance_next_funding_fee += funding_rate_fee * 10**18

            snapshot.binance_next_funding_fee = binance_next_funding_fee

    snapshot.users_paid_funding_fee = session.execute(
        select(func.coalesce(func.sum(Quote.fundingReceived), Decimal(0))).where(
            and_(
                Quote.blockNumber <= block.number,
                Quote.partyB == hedger_context.hedger_address,
                Quote.tenant == context.tenant,
            )
        )
    ).scalar_one()

    snapshot.users_received_funding_fee = session.execute(
        select(func.coalesce(func.sum(Quote.fundingPaid), Decimal(0))).where(
            and_(
                Quote.blockNumber <= block.number,
                Quote.partyB == hedger_context.hedger_address,
                Quote.tenant == context.tenant,
            )
        )
    ).scalar_one()

    contract_multicallable = Multicallable(snapshot_context.w3.to_checksum_address(context.symmio_address), SYMMIO_ABI, snapshot_context.w3)

    snapshot.hedger_contract_balance = contract_multicallable.balanceOf(
        [snapshot_context.w3.to_checksum_address(hedger_context.hedger_address)]
    ).call(block_identifier=block.number)[0]

    hedger_deposit = session.execute(
        select(func.coalesce(func.sum(BalanceChange.amount), Decimal(0))).where(
            and_(
                BalanceChange.collateral == context.symmio_collateral_address,
                BalanceChange.type == BalanceChangeType.DEPOSIT,
                BalanceChange.account_id == hedger_context.hedger_address,
                BalanceChange.tenant == context.tenant,
                BalanceChange.blockNumber <= block.number,
            )
        )
    ).scalar_one()

    snapshot.hedger_contract_deposit = hedger_deposit * 10 ** (18 - config.decimals) + hedger_context.contract_deposit_diff

    hedger_withdraw = session.execute(
        select(func.coalesce(func.sum(BalanceChange.amount), Decimal(0))).where(
            and_(
                BalanceChange.collateral == context.symmio_collateral_address,
                BalanceChange.type == BalanceChangeType.WITHDRAW,
                BalanceChange.account_id == hedger_context.hedger_address,
                BalanceChange.tenant == context.tenant,
                BalanceChange.blockNumber <= block.number,
            )
        )
    ).scalar_one()

    snapshot.hedger_contract_withdraw = hedger_withdraw * 10 ** (18 - config.decimals)

    affiliates_snapshots = []
    for affiliate in context.affiliates:
        s = get_last_affiliate_snapshot_for(context, session, affiliate.name, hedger_context.name, block)
        if s:
            affiliates_snapshots.append(s)

    snapshot.contract_profit = (
        snapshot.hedger_contract_balance
        + sum([snapshot.hedger_contract_allocated for snapshot in affiliates_snapshots])
        + sum([snapshot.hedger_upnl for snapshot in affiliates_snapshots])
        - snapshot.hedger_contract_deposit
        + snapshot.hedger_contract_withdraw
    )

    if has_binance_data:
        snapshot.binance_profit = snapshot.binance_total_balance - (snapshot.binance_deposit or Decimal(0))

    snapshot.earned_cva = sum([snapshot.earned_cva for snapshot in affiliates_snapshots])
    snapshot.loss_cva = sum([snapshot.loss_cva for snapshot in affiliates_snapshots])

    snapshot.liquidators_balance = Decimal(0)
    snapshot.liquidators_withdraw = Decimal(0)
    snapshot.liquidators_allocated = Decimal(0)
    checked_liquidators = set()
    for affiliate_snapshot in affiliates_snapshots:
        if affiliate_snapshot.liquidator_states:
            for state in affiliate_snapshot.liquidator_states:
                if state["address"] in checked_liquidators:
                    continue
                checked_liquidators.add(state["address"])
                snapshot.liquidators_balance += Decimal(state["balance"])
                snapshot.liquidators_withdraw += Decimal(state["withdraw"])
                snapshot.liquidators_allocated += Decimal(state["allocated"])

    snapshot.liquidators_profit = snapshot.liquidators_balance + snapshot.liquidators_allocated + snapshot.liquidators_withdraw

    snapshot.timestamp = block.datetime()
    snapshot.name = hedger_context.name
    snapshot.tenant = context.tenant
    snapshot.block_number = block.number
    print(snapshot)
    hedger_snapshot = HedgerSnapshot(**snapshot)
    hedger_snapshot.save(session)
    return hedger_snapshot
