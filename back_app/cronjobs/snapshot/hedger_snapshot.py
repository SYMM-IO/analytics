from datetime import datetime
from decimal import Decimal

import web3
from multicallable import Multicallable
from peewee import fn

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


def prepare_hedger_snapshot(config, context: Context, hedger_context: HedgerContext):
    print(f"----------------Prepare Hedger Snapshot Of {hedger_context.name}")
    from_time = datetime.fromtimestamp(context.from_unix_timestamp / 1000)

    snapshot = AttrDict()
    if hedger_context.utils.binance_client:
        total_transfers = (
            BinanceIncome.select(fn.SUM(BinanceIncome.amount))
            .where(
                BinanceIncome.type == "TRANSFER",
                BinanceIncome.tenant == context.tenant,
                BinanceIncome.hedger == hedger_context.name,
            )
            .scalar()
            or 0.0
        ) + (
            BinanceIncome.select(fn.SUM(BinanceIncome.amount))
            .where(
                BinanceIncome.type == "INTERNAL_TRANSFER",
                BinanceIncome.tenant == context.tenant,
                BinanceIncome.hedger == hedger_context.name,
            )
            .scalar()
            or 0.0
        )

        is_negative = total_transfers < 0
        snapshot.binance_deposit = (
            Decimal(
                -(abs(total_transfers) * 10**18)
                if is_negative
                else total_transfers * 10**18
            )
            + hedger_context.binance_deposit_diff
        )

        binance_account = hedger_context.utils.binance_client.futures_account(version=2)
        snapshot.binance_maintenance_margin = Decimal(
            float(binance_account["totalMaintMargin"]) * 10**18
        )
        snapshot.binance_total_balance = Decimal(
            float(binance_account["totalMarginBalance"]) * 10**18
        )
        snapshot.binance_account_health_ratio = (
            100
            - (snapshot.binance_maintenance_margin / snapshot.binance_total_balance)
            * 100
        )
        snapshot.binance_cross_upnl = (
            Decimal(binance_account["totalCrossUnPnl"]) * 10**18
        )
        snapshot.binance_av_balance = (
            Decimal(binance_account["availableBalance"]) * 10**18
        )
        snapshot.binance_total_initial_margin = (
            Decimal(binance_account["totalInitialMargin"]) * 10**18
        )
        snapshot.binance_max_withdraw_amount = (
            Decimal(binance_account["maxWithdrawAmount"]) * 10**18
        )
        snapshot.max_open_interest = Decimal(
            hedger_context.hedger_max_open_interest_ratio
            * snapshot.binance_max_withdraw_amount
        )
        snapshot.binance_trade_volume = (
            0
            if IGNORE_BINANCE_TRADE_VOLUME
            else Decimal(
                calculate_binance_trade_volume(context, hedger_context) * 10**18
            )
        )

        # ------------------------------------------
        # data.paid_funding_rate = PaidFundingRate.select(
        #     fn.Sum(PaidFundingRate.amount)
        # ).where(PaidFundingRate.timestamp > from_time, PaidFundingRate.amount < 0).scalar() or Decimal(0)

        snapshot.paid_funding_rate = BinanceIncome.select(
            fn.Sum(BinanceIncome.amount)
        ).where(
            BinanceIncome.timestamp > from_time,
            BinanceIncome.amount < 0,
            BinanceIncome.type == "FUNDING_FEE",
            BinanceIncome.tenant == context.tenant,
        ).scalar() or Decimal(
            0
        )

        snapshot.received_funding_rate = Quote.select(
            fn.Sum(Quote.fundingPaid)
        ).where(
            Quote.timestamp > from_time,
            Quote.partyB > hedger_context.hedger_address,
            Quote.tenant == context.tenant,
        ).scalar() or Decimal(
            0
        )

        positions = hedger_context.utils.binance_client.futures_position_information()
        open_positions = [p for p in positions if Decimal(p["notional"]) != 0]
        next_funding_rate = 0
        for pos in open_positions:
            notional, symbol, side = (
                Decimal(pos["notional"]),
                pos["symbol"],
                pos["positionSide"],
            )
            funding_rate = pos["fundingRate"] = real_time_funding_rate(symbol=symbol)
            funding_rate_fee = -1 * notional * funding_rate
            next_funding_rate += funding_rate_fee * 10**18

        snapshot.next_funding_rate = next_funding_rate

    w3 = web3.Web3(web3.Web3.HTTPProvider(context.rpc))
    contract_multicallable = Multicallable(
        w3.to_checksum_address(context.symmio_address), SYMMIO_ABI, w3
    )

    snapshot.hedger_contract_balance = contract_multicallable.balanceOf(
        [w3.to_checksum_address(hedger_context.hedger_address)]
    ).call()[0]

    hedger_deposit = BalanceChange.select(fn.Sum(BalanceChange.amount)).where(
        BalanceChange.collateral == context.symmio_collateral_address,
        BalanceChange.type == BalanceChangeType.DEPOSIT,
        BalanceChange.account == hedger_context.hedger_address,
        BalanceChange.tenant == context.tenant,
    ).scalar() or Decimal(0)

    snapshot.hedger_contract_deposit = (
        hedger_deposit * 10 ** (18 - config.decimals)
        + hedger_context.contract_deposit_diff
    )

    hedger_withdraw = BalanceChange.select(fn.Sum(BalanceChange.amount)).where(
        BalanceChange.collateral == context.symmio_collateral_address,
        BalanceChange.type == BalanceChangeType.WITHDRAW,
        BalanceChange.account == hedger_context.hedger_address,
        BalanceChange.tenant == context.tenant,
    ).scalar() or Decimal(0)

    snapshot.hedger_contract_withdraw = hedger_withdraw * 10 ** (18 - config.decimals)

    affiliates_snapshots = []
    for affiliate in context.affiliates:
        s = get_last_affiliate_snapshot_for(
            context, affiliate.name, hedger_context.name
        )
        if s:
            affiliates_snapshots.append(s)

    snapshot.contract_profit = (
        snapshot.hedger_contract_balance
        + sum([snapshot.hedger_contract_allocated for snapshot in affiliates_snapshots])
        + sum([snapshot.hedger_upnl for snapshot in affiliates_snapshots])
        - snapshot.hedger_contract_deposit
        + snapshot.hedger_contract_withdraw
    )

    if "binance_deposit" in snapshot:
        snapshot.binance_profit = snapshot.binance_total_balance - (
            snapshot.binance_deposit or Decimal(0)
        )

    snapshot.earned_cva = sum(
        [snapshot.earned_cva for snapshot in affiliates_snapshots]
    )
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
    hedger_snapshot = HedgerSnapshot.create(**snapshot)
    return hedger_snapshot
