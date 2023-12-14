from datetime import datetime, timedelta
from decimal import Decimal

import requests
import web3
from multicallable import Multicallable
from peewee import fn

from app.models import (
    Account,
    AffiliateSnapshot,
    DailyHistory,
    Quote,
    Symbol,
    TradeHistory,
    BalanceChange,
    BalanceChangeType,
    BinanceIncome,
    HedgerSnapshot,
)
from config.settings import Context, symmio_abi, AffiliateContext, HedgerContext
from cronjobs.binance_trade_volume import calculate_binance_trade_volume
from cronjobs.data_loaders import (
    load_accounts,
    load_daily_histories,
    load_quotes,
    load_symbols,
    load_trade_histories,
    load_users,
    load_balance_changes,
)
from utils.attr_dict import AttrDict
from utils.common_utils import load_config


def real_time_funding_rate(symbol: str) -> Decimal:
    url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}"
    response = requests.get(url)
    funding_rate = Decimal(0)
    if response.status_code == 200:
        data = response.json()
        funding_rate = Decimal(data["lastFundingRate"])
    else:
        print("An error occurred:", response.status_code)
    return funding_rate


def fetch_snapshot(context: Context):
    config = load_config(context)
    current_time = datetime.utcnow() - timedelta(minutes=5)  # for subgraph sync time

    load_users(config, context)
    load_symbols(config, context)
    load_accounts(config, context)
    load_balance_changes(config, context)
    load_quotes(config, context)
    load_trade_histories(config, context)
    load_daily_histories(config, context)

    print(f"{context.tenant}: Data loaded...\nPreparing snapshot data...")

    for affiliate_context in context.affiliates:
        prepare_affiliate_snapshot(config, context, affiliate_context)
    for hedger_context in context.hedgers:
        prepare_hedger_snapshot(config, context, hedger_context)

    config = load_config(context)  # Configuration may have changed during this method
    config.lastSnapshotTimestamp = current_time
    config.upsert()


def prepare_affiliate_snapshot(
    config, context: Context, affiliate_context: AffiliateContext
):
    from_time = datetime.fromtimestamp(context.from_unix_timestamp / 1000)
    hedger_context = context.hedger_for_affiliate(affiliate_context.name)
    snapshot = AttrDict()
    q_counts = (
        Quote.select(Quote.quoteStatus, fn.Count(Quote.id).alias("count"))
        .join(Account)
        .where(
            Quote.timestamp > from_time,
            Account.accountSource == affiliate_context.symmio_multi_account,
            Quote.tenant == context.tenant,
        )
        .group_by(Quote.quoteStatus)
    )
    status_quotes = {}
    for item in q_counts:
        status_quotes[item.quoteStatus] = item.count
    snapshot.status_quotes = status_quotes

    # ------------------------------------------
    party_b_closed_quotes = (
        Quote.select()
        .join(Account)
        .where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            Quote.partyB == hedger_context.hedger_address,
            Quote.quoteStatus == 7,
            Quote.timestamp > from_time,
            Quote.tenant == context.tenant,
        )
    )
    snapshot.pnl_of_closed = Decimal(0)
    for quote in party_b_closed_quotes:
        if quote.positionType == "0":
            snapshot.pnl_of_closed -= Decimal(
                int(quote.quantity)
                * (int(quote.avgClosedPrice) - int(quote.openPrice))
                / 10**18
            )
        else:
            snapshot.pnl_of_closed -= Decimal(
                int(quote.quantity)
                * (int(quote.openPrice) - int(quote.avgClosedPrice))
                / 10**18
            )

    party_b_liquidated_quotes = (
        Quote.select()
        .join(Account)
        .where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            Quote.partyB == hedger_context.hedger_address,
            Quote.quoteStatus == 8,
            Quote.timestamp > from_time,
            Quote.tenant == context.tenant,
        )
    )
    snapshot.pnl_of_liquidated = Decimal(0)
    for quote in party_b_liquidated_quotes:
        if quote.positionType == "0":
            snapshot.pnl_of_liquidated -= Decimal(
                int(quote.quantity)
                * (int(quote.avgClosedPrice) - int(quote.openPrice))
                / 10**18
            )
        else:
            snapshot.pnl_of_liquidated -= Decimal(
                int(quote.quantity)
                * (int(quote.openPrice) - int(quote.avgClosedPrice))
                / 10**18
            )

    # ------------------------------------------

    prices = hedger_context.utils.binance_client.futures_mark_price()
    prices_map = {}
    for p in prices:
        prices_map[p["symbol"]] = p["markPrice"]

    party_b_opened_quotes = (
        Quote.select(
            Quote.id,
            Quote.quantity,
            Quote.closedAmount,
            Quote.openPrice,
            Quote.positionType,
            Symbol.name,
        )
        .join(Symbol)
        .switch(Quote)
        .join(Account)
        .where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            Quote.timestamp > from_time,
            Quote.partyB == hedger_context.hedger_address,
            (
                (Quote.quoteStatus == 4)
                | (Quote.quoteStatus == 5)
                | (Quote.quoteStatus == 6)
            ),
            Quote.tenant == context.tenant,
        )
    )

    subgraph_open_quotes = []
    snapshot.hedger_upnl = Decimal(0)
    for quote in party_b_opened_quotes:
        key = f"{quote.id}-{quote.openPrice}-{quote.closedAmount}-{quote.quantity}"
        subgraph_open_quotes.append(key)
        side_sign = 1 if quote.positionType == "0" else -1
        current_price = Decimal(prices_map[quote.symbolId.name]) * 10**18
        snapshot.hedger_upnl += (
            side_sign
            * (quote.openPrice - current_price)
            * (quote.quantity - quote.closedAmount)
            // 10**18
        )

    # ------------------------------------------
    closed_trade_histories = (
        TradeHistory.select()
        .join(Account)
        .where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            TradeHistory.quoteStatus == 7,
            TradeHistory.timestamp > from_time,
            TradeHistory.tenant == context.tenant,
        )
    )
    snapshot.closed_notional_value = sum(
        int(th.volume) for th in closed_trade_histories
    )

    liquidated_trade_histories = (
        TradeHistory.select()
        .join(Account)
        .where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            TradeHistory.quoteStatus == 8,
            TradeHistory.timestamp > from_time,
            TradeHistory.tenant == context.tenant,
        )
    )
    snapshot.liquidated_notional_value = sum(
        int(th.volume) for th in liquidated_trade_histories
    )

    opened_trade_histories = (
        TradeHistory.select()
        .join(Account)
        .where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            TradeHistory.quoteStatus == 4,
            TradeHistory.timestamp > from_time,
            TradeHistory.tenant == context.tenant,
        )
    )
    snapshot.opened_notional_value = sum(
        int(th.volume) for th in opened_trade_histories
    )

    # ------------------------------------------

    party_b_liquidated_party_a_quotes = (
        Quote.select()
        .join(Account)
        .where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            Quote.partyB == hedger_context.hedger_address,
            Quote.quoteStatus == 8,
            Quote.liquidatedSide == 0,
            Quote.timestamp > from_time,
            Quote.tenant == context.tenant,
        )
    )
    snapshot.earned_cva = sum(int(q.cva) for q in party_b_liquidated_party_a_quotes)

    party_b_liquidated_party_b_quotes = (
        Quote.select()
        .join(Account)
        .where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            Quote.partyB == hedger_context.hedger_address,
            Quote.quoteStatus == 8,
            Quote.liquidatedSide == 1,
            Quote.timestamp > from_time,
            Quote.tenant == context.tenant,
        )
    )
    snapshot.loss_cva = sum(int(q.cva) for q in party_b_liquidated_party_b_quotes)

    # ------------------------------------------
    w3 = web3.Web3(web3.Web3.HTTPProvider(context.rpc))
    contract_multicallable = Multicallable(
        w3.to_checksum_address(context.symmio_address), symmio_abi, w3
    )
    all_accounts = list(
        Account.select(Account.id).where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            Account.tenant == context.tenant,
        )
    )
    pages_count = len(all_accounts) // 100 if len(all_accounts) > 0 else 100
    hedger_addr = w3.to_checksum_address(hedger_context.hedger_address)
    snapshot.hedger_contract_allocated = Decimal(
        sum(
            contract_multicallable.allocatedBalanceOfPartyB(
                [(hedger_addr, w3.to_checksum_address(a.id)) for a in all_accounts]
            ).call(n=pages_count)
        )
    )

    all_accounts_deposit = BalanceChange.select(fn.Sum(BalanceChange.amount)).join(
        Account
    ).where(
        Account.accountSource == affiliate_context.symmio_multi_account,
        BalanceChange.type == BalanceChangeType.DEPOSIT,
        BalanceChange.collateral == context.symmio_collateral_address,
        BalanceChange.tenant == context.tenant,
    ).scalar() or Decimal(
        0
    )
    snapshot.all_contract_deposit = all_accounts_deposit * 10 ** (18 - config.decimals)

    all_accounts_withdraw = BalanceChange.select(fn.Sum(BalanceChange.amount)).join(
        Account
    ).where(
        Account.accountSource == affiliate_context.symmio_multi_account,
        BalanceChange.type == BalanceChangeType.WITHDRAW,
        BalanceChange.collateral == context.symmio_collateral_address,
        BalanceChange.tenant == context.tenant,
    ).scalar() or Decimal(
        0
    )
    snapshot.all_contract_withdraw = all_accounts_withdraw * 10 ** (
        18 - config.decimals
    )

    ppp = contract_multicallable.getPartyAOpenPositions(
        [(w3.to_checksum_address(a.id), 0, 100) for a in all_accounts]
    ).call(n=pages_count)

    print(f"{context.tenant}: Diff of open quotes with subgraph")
    for pp in ppp:
        for quote in pp:
            key = f"{context.tenant}_{quote[0]}-{quote[5]}-{quote[9]}-{quote[8]}"
            if key not in subgraph_open_quotes:
                db_quote = Quote.get_or_none(
                    Quote.id == quote[0], Quote.tenant == context.tenant
                )
                if db_quote:
                    print(
                        f"{context.tenant}: {key}:{db_quote.id}-{db_quote.openPrice}-{db_quote.closedAmount}-{db_quote.quantity}"
                    )
                else:
                    print(
                        f"{context.tenant}: Not found opened quote in subgraph: {key}"
                    )
    print("----------------------------------")

    # ------------------------------------------

    snapshot.accounts_count = (
        Account.select(fn.count(Account.id))
        .where(
            Account.timestamp > from_time,
            Account.accountSource == affiliate_context.symmio_multi_account,
            Account.tenant == context.tenant,
        )
        .scalar()
    ) or 0
    active_timestamp = datetime.utcnow() - timedelta(hours=48)
    snapshot.active_accounts = (
        Account.select(fn.count(Account.id))
        .where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            Account.lastActivityTimestamp > active_timestamp,
            Account.timestamp > from_time,
            Account.tenant == context.tenant,
        )
        .scalar()
    ) or 0
    snapshot.users_count = (
        Account.select(fn.COUNT(fn.DISTINCT(Account.user)))
        .where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            Account.timestamp > from_time,
            Account.tenant == context.tenant,
        )
        .scalar()
    ) or 0
    snapshot.active_users = (
        Account.select(fn.COUNT(fn.DISTINCT(Account.user)))
        .where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            Account.lastActivityTimestamp > active_timestamp,
            Account.timestamp > from_time,
            Account.tenant == context.tenant,
        )
        .scalar()
    ) or 0

    # ------------------------------------------

    for liquidator in affiliate_context.symmio_liquidators:
        account_withdraw = BalanceChange.select(fn.Sum(BalanceChange.amount)).where(
            BalanceChange.collateral == context.symmio_collateral_address,
            BalanceChange.type == BalanceChangeType.WITHDRAW,
            BalanceChange.account == liquidator,
            BalanceChange.tenant == context.tenant,
        ).scalar() or Decimal(0)
        liquidator_state = {
            "address": liquidator,
            "withdraw": int(account_withdraw) * 10 ** (18 - config.decimals),
            "balance": contract_multicallable.balanceOf(
                [w3.to_checksum_address(liquidator)]
            ).call()[0],
            "allocated": contract_multicallable.balanceInfoOfPartyA(
                [w3.to_checksum_address(liquidator)]
            ).call()[0][0],
        }
        if "liquidator_states" not in snapshot:
            snapshot.liquidator_states = []
        snapshot.liquidator_states.append(liquidator_state)

    # ------------------------------------------
    snapshot.platform_fee = (
        DailyHistory.select(fn.Sum(DailyHistory.platformFee))
        .where(
            DailyHistory.timestamp > from_time,
            DailyHistory.accountSource == affiliate_context.symmio_multi_account,
            DailyHistory.tenant == context.tenant,
        )
        .scalar()
    ) or 0

    snapshot.trade_volume = (
        DailyHistory.select(fn.Sum(DailyHistory.tradeVolume))
        .where(
            DailyHistory.timestamp > from_time,
            DailyHistory.accountSource == affiliate_context.symmio_multi_account,
            DailyHistory.tenant == context.tenant,
        )
        .scalar()
    ) or 0

    snapshot.timestamp = datetime.utcnow()
    snapshot.name = affiliate_context.name
    snapshot.hedger_name = hedger_context.name
    snapshot.account_source = affiliate_context.symmio_multi_account
    snapshot.tenant = context.tenant
    affiliate_snapshot = AffiliateSnapshot.create(**snapshot)
    return affiliate_snapshot


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
    snapshot.binance_trade_volume = Decimal(
        calculate_binance_trade_volume(context, hedger_context) * 10**18
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
        w3.to_checksum_address(context.symmio_address), symmio_abi, w3
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
