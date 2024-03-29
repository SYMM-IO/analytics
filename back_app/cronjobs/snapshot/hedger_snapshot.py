from datetime import datetime
from decimal import Decimal

import web3
from multicallable import Multicallable
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from app.models import (
    BalanceChange,
    BalanceChangeType,
    BinanceIncome,
    HedgerSnapshot, Quote,
)
from config.settings import (
    Context,
    SYMMIO_ABI,
    HedgerContext,
    IGNORE_BINANCE_TRADE_VOLUME,
)
from cronjobs.binance_trade_volume import calculate_binance_trade_volume
from services.binance_service import real_time_funding_rate
from services.snaphshot_service import get_last_affiliate_snapshot_for
from utils.attr_dict import AttrDict


def prepare_hedger_snapshot(config, context: Context, session: Session, hedger_context: HedgerContext):
    print(f"----------------Prepare Hedger Snapshot Of {hedger_context.name}")
    has_binance_data = hedger_context.utils.binance_client is not None

    snapshot = AttrDict()
    if has_binance_data:
        transfer_sum = session.execute(
            select(func.coalesce(func.sum(BinanceIncome.amount), 0)).where(
                and_(
                    BinanceIncome.type == "TRANSFER",
                    BinanceIncome.tenant == context.tenant,
                    BinanceIncome.hedger == hedger_context.name,
                )
            )
        ).scalar_one()

        internal_transfer_sum = session.execute(
            select(func.coalesce(func.sum(BinanceIncome.amount), 0)).where(
                and_(
                    BinanceIncome.type == "INTERNAL_TRANSFER",
                    BinanceIncome.tenant == context.tenant,
                    BinanceIncome.hedger == hedger_context.name,
                )
            )
        ).scalar_one()

        total_transfers = transfer_sum + internal_transfer_sum

        is_negative = total_transfers < 0
        snapshot.binance_deposit = (
                Decimal(
                    -(abs(total_transfers) * 10 ** 18)
                    if is_negative
                    else total_transfers * 10 ** 18
                )
                + hedger_context.binance_deposit_diff
        )

        binance_account = hedger_context.utils.binance_client.futures_account(version=2)
        snapshot.binance_maintenance_margin = Decimal(
            float(binance_account["totalMaintMargin"]) * 10 ** 18
        )
        snapshot.binance_total_balance = Decimal(
            float(binance_account["totalMarginBalance"]) * 10 ** 18
        )
        snapshot.binance_account_health_ratio = (
                100
                - (snapshot.binance_maintenance_margin / snapshot.binance_total_balance)
                * 100
        )
        snapshot.binance_cross_upnl = (
                Decimal(binance_account["totalCrossUnPnl"]) * 10 ** 18
        )
        snapshot.binance_av_balance = (
                Decimal(binance_account["availableBalance"]) * 10 ** 18
        )
        snapshot.binance_total_initial_margin = (
                Decimal(binance_account["totalInitialMargin"]) * 10 ** 18
        )
        snapshot.binance_max_withdraw_amount = (
                Decimal(binance_account["maxWithdrawAmount"]) * 10 ** 18
        )
        snapshot.max_open_interest = Decimal(
            hedger_context.hedger_max_open_interest_ratio
            * snapshot.binance_max_withdraw_amount
        )
        snapshot.binance_trade_volume = (
            0
            if IGNORE_BINANCE_TRADE_VOLUME
            else Decimal(
                calculate_binance_trade_volume(context, hedger_context) * 10 ** 18
            )
        )

        # ------------------------------------------
        # data.paid_funding_rate = PaidFundingRate.select(
        #     fn.Sum(PaidFundingRate.amount)
        # ).where(PaidFundingRate.timestamp > from_time, PaidFundingRate.amount < 0).scalar() or Decimal(0)

        snapshot.binance_paid_funding_fee = session.execute(
            select(func.coalesce(func.sum(BinanceIncome.amount), Decimal(0))).where(
                and_(
                    BinanceIncome.amount < 0,
                    BinanceIncome.type == "FUNDING_FEE",
                    BinanceIncome.tenant == context.tenant,
                )
            )
        ).scalar_one()

        snapshot.binance_received_funding_fee = session.execute(
            select(func.coalesce(func.sum(BinanceIncome.amount), Decimal(0))).where(
                and_(
                    BinanceIncome.amount > 0,
                    BinanceIncome.type == "FUNDING_FEE",
                    BinanceIncome.tenant == context.tenant,
                )
            )
        ).scalar_one()

        positions = hedger_context.utils.binance_client.futures_position_information()
        open_positions = [p for p in positions if Decimal(p["notional"]) != 0]
        binance_next_funding_fee = 0
        for pos in open_positions:
            notional, symbol, side = (
                Decimal(pos["notional"]),
                pos["symbol"],
                pos["positionSide"],
            )
            funding_rate = pos["fundingRate"] = real_time_funding_rate(symbol=symbol)
            funding_rate_fee = -1 * notional * funding_rate
            binance_next_funding_fee += funding_rate_fee * 10 ** 18

        snapshot.binance_next_funding_fee = binance_next_funding_fee

    snapshot.users_paid_funding_fee = session.execute(
        select(func.coalesce(func.sum(Quote.fundingReceived), Decimal(0))).where(
            and_(
                Quote.partyB == hedger_context.hedger_address,
                Quote.tenant == context.tenant,
            )
        )
    ).scalar_one()

    snapshot.users_received_funding_fee = session.execute(
        select(func.coalesce(func.sum(Quote.fundingPaid), Decimal(0))).where(
            and_(
                Quote.partyB == hedger_context.hedger_address,
                Quote.tenant == context.tenant,
            )
        )
    ).scalar_one()

    w3 = web3.Web3(web3.Web3.HTTPProvider(context.rpc))
    contract_multicallable = Multicallable(w3.to_checksum_address(context.symmio_address), SYMMIO_ABI, w3)

    snapshot.hedger_contract_balance = contract_multicallable.balanceOf(
        [w3.to_checksum_address(hedger_context.hedger_address)]
    ).call()[0]

    hedger_deposit = session.execute(
        select(func.coalesce(func.sum(BalanceChange.amount), Decimal(0))).where(
            and_(
                BalanceChange.collateral == context.symmio_collateral_address,
                BalanceChange.type == BalanceChangeType.DEPOSIT,
                BalanceChange.account_id == hedger_context.hedger_address,
                BalanceChange.tenant == context.tenant,
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
            )
        )
    ).scalar_one()

    snapshot.hedger_contract_withdraw = hedger_withdraw * 10 ** (18 - config.decimals)

    affiliates_snapshots = []
    for affiliate in context.affiliates:
        s = get_last_affiliate_snapshot_for(context, session, affiliate.name, hedger_context.name)
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

    snapshot.liquidators_profit = (
            snapshot.liquidators_balance
            + snapshot.liquidators_allocated
            + snapshot.liquidators_withdraw
    )

    snapshot.timestamp = datetime.utcnow()
    snapshot.name = hedger_context.name
    snapshot.tenant = context.tenant
    hedger_snapshot = HedgerSnapshot(**snapshot)
    hedger_snapshot.save(session)
    return hedger_snapshot
