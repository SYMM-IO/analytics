from datetime import datetime
from decimal import Decimal

import web3
from multicallable import Multicallable
from peewee import fn

from app.models import (
    BalanceChange,
    BalanceChangeType,
    BinanceIncome,
    HedgerSnapshot,
)
from config.settings import (
    Context,
    SYMMIO_ABI,
    HedgerContext,
    IGNORE_BINANCE_TRADE_VOLUME,
)
from cronjobs.binance_trade_volume import calculate_binance_trade_volume
from utils.attr_dict import AttrDict


def prepare_hedger_snapshot(config, context: Context, hedger_context: HedgerContext):
    from_time = datetime.fromtimestamp(context.from_unix_timestamp / 1000)

    snapshot = AttrDict()
    binance_account = hedger_context.utils.binance_client.futures_account(version=2)
    snapshot.binance_maintenance_margin = Decimal(
        float(binance_account["totalMaintMargin"]) * 10**18
    )
    snapshot.binance_total_balance = Decimal(
        float(binance_account["totalMarginBalance"]) * 10**18
    )
    snapshot.binance_account_health_ratio = (
        100
        - (snapshot.binance_maintenance_margin / snapshot.binance_total_balance) * 100
    )
    snapshot.binance_cross_upnl = Decimal(binance_account["totalCrossUnPnl"]) * 10**18
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
    snapshot.binance_deposit = config.binanceDeposit
    snapshot.binance_trade_volume = (
        0
        if IGNORE_BINANCE_TRADE_VOLUME
        else Decimal(calculate_binance_trade_volume(context, hedger_context) * 10**18)
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
        hedger_deposit * 10 ** (18 - config.decimals) - hedger_context.deposit_diff
    )

    hedger_withdraw = BalanceChange.select(fn.Sum(BalanceChange.amount)).where(
        BalanceChange.collateral == context.symmio_collateral_address,
        BalanceChange.type == BalanceChangeType.WITHDRAW,
        BalanceChange.account == hedger_context.hedger_address,
        BalanceChange.tenant == context.tenant,
    ).scalar() or Decimal(0)
    snapshot.hedger_contract_withdraw = hedger_withdraw * 10 ** (18 - config.decimals)

    snapshot.timestamp = datetime.utcnow()
    snapshot.name = hedger_context.name
    snapshot.tenant = context.tenant
    hedger_snapshot = HedgerSnapshot.create(**snapshot)
    return hedger_snapshot
