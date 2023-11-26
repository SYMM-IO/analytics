from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

import requests
import web3
from multicallable import Multicallable
from peewee import fn

from app.models import (
    Account,
    AggregateData,
    DailyHistory,
    Quote,
    Symbol,
    TradeHistory,
    BalanceChange,
    BalanceChangeType,
    BinanceIncome,
)
from config.settings import erc20_abi, Context, symmio_abi
from cronjobs.binance_trade_volume import calculate_binance_trade_volume
from cronjobs.bot.analytics_bot import prepare_and_report_data
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


def fetch_aggregate_data(context: Context):
    config = load_config(context)
    current_time = datetime.utcnow() - timedelta(minutes=4)  # for subgraph sync time

    load_users(config, context)
    load_symbols(config, context)
    load_accounts(config, context)
    load_balance_changes(config, context)
    load_quotes(config, context)
    load_trade_histories(config, context)
    load_daily_histories(config, context)

    print(f"{context.tenant}: Data loaded...\nPreparing aggregate data...")
    aggregate_data = prepare_aggregate_data(config, context)

    config = load_config(context)  # Configuration may have changed during this method
    config.updateTimestamp = current_time
    config.upsert()

    prepare_and_report_data(context, aggregate_data)


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


def prepare_aggregate_data(config, context: Context):
    from_time = datetime.fromtimestamp(context.from_unix_timestamp / 1000)

    data = AttrDict()
    q_counts = (
        Quote.select(Quote.quoteStatus, fn.Count(Quote.id).alias("count"))
        .join(Account)
        .where(
            Quote.timestamp > from_time,
            Account.accountSource == context.symmio_multi_account,
            Quote.tenant == context.tenant,
        )
        .group_by(Quote.quoteStatus)
    )
    status_quotes = {}
    for item in q_counts:
        status_quotes[item.quoteStatus] = item.count
    data.status_quotes = status_quotes

    # ------------------------------------------
    party_b_closed_quotes = (
        Quote.select()
        .join(Account)
        .where(
            Account.accountSource == context.symmio_multi_account,
            Quote.partyB == context.hedger_address,
            Quote.quoteStatus == 7,
            Quote.timestamp > from_time,
            Quote.tenant == context.tenant,
        )
    )
    data.pnl_of_closed = Decimal(0)
    for quote in party_b_closed_quotes:
        if quote.positionType == "0":
            data.pnl_of_closed -= Decimal(
                int(quote.quantity)
                * (int(quote.avgClosedPrice) - int(quote.openPrice))
                / 10**18
            )
        else:
            data.pnl_of_closed -= Decimal(
                int(quote.quantity)
                * (int(quote.openPrice) - int(quote.avgClosedPrice))
                / 10**18
            )

    party_b_liquidated_quotes = (
        Quote.select()
        .join(Account)
        .where(
            Account.accountSource == context.symmio_multi_account,
            Quote.partyB == context.hedger_address,
            Quote.quoteStatus == 8,
            Quote.timestamp > from_time,
            Quote.tenant == context.tenant,
        )
    )
    data.pnl_of_liquidated = Decimal(0)
    for quote in party_b_liquidated_quotes:
        if quote.positionType == "0":
            data.pnl_of_liquidated -= Decimal(
                int(quote.quantity)
                * (int(quote.avgClosedPrice) - int(quote.openPrice))
                / 10**18
            )
        else:
            data.pnl_of_liquidated -= Decimal(
                int(quote.quantity)
                * (int(quote.openPrice) - int(quote.avgClosedPrice))
                / 10**18
            )

    # ------------------------------------------

    prices = context.utils.binance_client.futures_mark_price()
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
            Account.accountSource == context.symmio_multi_account,
            Quote.timestamp > from_time,
            Quote.partyB == context.hedger_address,
            (
                (Quote.quoteStatus == 4)
                | (Quote.quoteStatus == 5)
                | (Quote.quoteStatus == 6)
            ),
            Quote.tenant == context.tenant,
        )
    )

    subgraph_open_quotes = []
    data.hedger_upnl = Decimal(0)
    for quote in party_b_opened_quotes:
        key = f"{quote.id}-{quote.openPrice}-{quote.closedAmount}-{quote.quantity}"
        subgraph_open_quotes.append(key)
        side_sign = 1 if quote.positionType == "0" else -1
        current_price = Decimal(prices_map[quote.symbolId.name]) * 10**18
        data.hedger_upnl += (
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
            Account.accountSource == context.symmio_multi_account,
            TradeHistory.quoteStatus == 7,
            TradeHistory.timestamp > from_time,
            TradeHistory.tenant == context.tenant,
        )
    )
    data.closed_notional_value = sum(int(th.volume) for th in closed_trade_histories)

    liquidated_trade_histories = (
        TradeHistory.select()
        .join(Account)
        .where(
            Account.accountSource == context.symmio_multi_account,
            TradeHistory.quoteStatus == 8,
            TradeHistory.timestamp > from_time,
            TradeHistory.tenant == context.tenant,
        )
    )
    data.liquidated_notional_value = sum(
        int(th.volume) for th in liquidated_trade_histories
    )

    opened_trade_histories = (
        TradeHistory.select()
        .join(Account)
        .where(
            Account.accountSource == context.symmio_multi_account,
            TradeHistory.quoteStatus == 4,
            TradeHistory.timestamp > from_time,
            TradeHistory.tenant == context.tenant,
        )
    )
    data.opened_notional_value = sum(int(th.volume) for th in opened_trade_histories)

    # ------------------------------------------

    party_b_liquidated_party_a_quotes = (
        Quote.select()
        .join(Account)
        .where(
            Account.accountSource == context.symmio_multi_account,
            Quote.partyB == context.hedger_address,
            Quote.quoteStatus == 8,
            Quote.liquidatedSide == 0,
            Quote.timestamp > from_time,
            Quote.tenant == context.tenant,
        )
    )
    data.earned_cva = sum(int(q.cva) for q in party_b_liquidated_party_a_quotes)

    party_b_liquidated_party_b_quotes = (
        Quote.select()
        .join(Account)
        .where(
            Account.accountSource == context.symmio_multi_account,
            Quote.partyB == context.hedger_address,
            Quote.quoteStatus == 8,
            Quote.liquidatedSide == 1,
            Quote.timestamp > from_time,
            Quote.tenant == context.tenant,
        )
    )
    data.loss_cva = sum(int(q.cva) for q in party_b_liquidated_party_b_quotes)

    # ------------------------------------------

    w3 = web3.Web3(web3.Web3.HTTPProvider(context.rpc))
    contract_multicallable = Multicallable(
        w3.to_checksum_address(context.symmio_address), symmio_abi, w3
    )
    data.hedger_contract_balance = contract_multicallable.balanceOf(
        [w3.to_checksum_address(context.hedger_address)]
    ).call()[0]
    hedger_deposit = BalanceChange.select(fn.Sum(BalanceChange.amount)).where(
        BalanceChange.collateral == context.symmio_collateral_address,
        BalanceChange.type == BalanceChangeType.DEPOSIT,
        BalanceChange.account == context.hedger_address,
        BalanceChange.tenant == context.tenant,
    ).scalar() or Decimal(0)
    data.hedger_contract_deposit = (
        hedger_deposit * 10 ** (18 - config.decimals) - context.deposit_diff
    )

    hedger_withdraw = BalanceChange.select(fn.Sum(BalanceChange.amount)).where(
        BalanceChange.collateral == context.symmio_collateral_address,
        BalanceChange.type == BalanceChangeType.WITHDRAW,
        BalanceChange.account == context.hedger_address,
        BalanceChange.tenant == context.tenant,
    ).scalar() or Decimal(0)
    data.hedger_contract_withdraw = hedger_withdraw * 10 ** (18 - config.decimals)

    all_accounts = list(
        Account.select(Account.id).where(
            Account.accountSource == context.symmio_multi_account,
            Account.tenant == context.tenant,
        )
    )
    pages_count = len(all_accounts) // 100 if len(all_accounts) > 0 else 100
    hedger_addr = w3.to_checksum_address(context.hedger_address)
    data.hedger_contract_allocated = Decimal(
        sum(
            contract_multicallable.allocatedBalanceOfPartyB(
                [(hedger_addr, w3.to_checksum_address(a.id)) for a in all_accounts]
            ).call(n=pages_count)
        )
    )

    all_accounts_deposit = BalanceChange.select(fn.Sum(BalanceChange.amount)).join(
        Account
    ).where(
        Account.accountSource == context.symmio_multi_account,
        BalanceChange.type == BalanceChangeType.DEPOSIT,
        BalanceChange.collateral == context.symmio_collateral_address,
        BalanceChange.tenant == context.tenant,
    ).scalar() or Decimal(
        0
    )
    data.all_contract_deposit = all_accounts_deposit * 10 ** (18 - config.decimals)

    all_accounts_withdraw = BalanceChange.select(fn.Sum(BalanceChange.amount)).join(
        Account
    ).where(
        Account.accountSource == context.symmio_multi_account,
        BalanceChange.type == BalanceChangeType.WITHDRAW,
        BalanceChange.collateral == context.symmio_collateral_address,
        BalanceChange.tenant == context.tenant,
    ).scalar() or Decimal(
        0
    )
    data.all_contract_withdraw = all_accounts_withdraw * 10 ** (18 - config.decimals)

    # Read contract balance of contract
    w3 = web3.Web3(web3.Web3.HTTPProvider(context.rpc))
    collateral_contract = w3.eth.contract(
        address=w3.to_checksum_address(context.symmio_collateral_address), abi=erc20_abi
    )

    data.contract_balance = collateral_contract.functions.balanceOf(
        w3.to_checksum_address(context.symmio_address)
    ).call() * 10 ** (18 - config.decimals)

    ppp = contract_multicallable.getPartyAOpenPositions(
        [(w3.to_checksum_address(a.id), 0, 100) for a in all_accounts]
    ).call(n=pages_count)

    print(f"{context.tenant}: Diff of open quotes with subgraph")
    for pp in ppp:
        for quote in pp:
            key = f"{quote[0]}-{quote[5]}-{quote[9]}-{quote[8]}"
            if key not in subgraph_open_quotes:
                db_quote = Quote.get_or_none(
                    Quote.id == quote[0], Quote.tenant == context.tenant
                )
                if db_quote:
                    print(
                        f"{context.tenant}: {key}:{db_quote.id}-{db_quote.openPrice}-{db_quote.closedAmount}-{db_quote.quantity}"
                    )
                else:
                    print(f"{context.tenant}: Not found opened quote in subgraph: {key}")
    print("----------------------------------")

    # ------------------------------------------

    data.accounts_count = (
        Account.select(fn.count(Account.id))
        .where(
            Account.timestamp > from_time,
            Account.accountSource == context.symmio_multi_account,
            Account.tenant == context.tenant,
        )
        .scalar()
    ) or 0
    active_timestamp = datetime.utcnow() - timedelta(hours=48)
    data.active_accounts = (
        Account.select(fn.count(Account.id))
        .where(
            Account.accountSource == context.symmio_multi_account,
            Account.lastActivityTimestamp > active_timestamp,
            Account.timestamp > from_time,
            Account.tenant == context.tenant,
        )
        .scalar()
    ) or 0
    data.users_count = (
        Account.select(fn.COUNT(fn.DISTINCT(Account.user)))
        .where(
            Account.accountSource == context.symmio_multi_account,
            Account.timestamp > from_time,
            Account.tenant == context.tenant,
        )
        .scalar()
    ) or 0
    data.active_users = (
        Account.select(fn.COUNT(fn.DISTINCT(Account.user)))
        .where(
            Account.accountSource == context.symmio_multi_account,
            Account.lastActivityTimestamp > active_timestamp,
            Account.timestamp > from_time,
            Account.tenant == context.tenant,
        )
        .scalar()
    ) or 0

    # ------------------------------------------

    for liquidator in context.symmio_liquidators:
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
        if "liquidator_states" not in data:
            data.liquidator_states = []
        data.liquidator_states.append(liquidator_state)

    # ------------------------------------------
    data.platform_fee = (
        DailyHistory.select(fn.Sum(DailyHistory.platformFee))
        .where(
            DailyHistory.timestamp > from_time,
            DailyHistory.accountSource == context.symmio_multi_account,
            DailyHistory.tenant == context.tenant,
        )
        .scalar()
    ) or 0

    data.trade_volume = (
        DailyHistory.select(fn.Sum(DailyHistory.tradeVolume))
        .where(
            DailyHistory.timestamp > from_time,
            DailyHistory.accountSource == context.symmio_multi_account,
            DailyHistory.tenant == context.tenant,
        )
        .scalar()
    ) or 0
    # ------------------------------------------

    binance_account = context.utils.binance_client.futures_account(version=2)
    data.binance_maintenance_margin = Decimal(
        float(binance_account["totalMaintMargin"]) * 10**18
    )
    data.binance_total_balance = Decimal(
        float(binance_account["totalMarginBalance"]) * 10**18
    )
    data.binance_account_health_ratio = (
        100 - (data.binance_maintenance_margin / data.binance_total_balance) * 100
    )
    data.binance_cross_upnl = Decimal(binance_account["totalCrossUnPnl"]) * 10**18
    data.binance_av_balance = Decimal(binance_account["availableBalance"]) * 10**18
    data.binance_total_initial_margin = (
        Decimal(binance_account["totalInitialMargin"]) * 10**18
    )
    data.binance_max_withdraw_amount = (
        Decimal(binance_account["maxWithdrawAmount"]) * 10**18
    )
    data.max_open_interest = Decimal(
        context.hedger_max_open_interest_ratio * data.binance_max_withdraw_amount
    )
    data.binance_deposit = config.binanceDeposit
    data.binance_trade_volume = Decimal(calculate_binance_trade_volume() * 10**18)

    # ------------------------------------------
    # data.paid_funding_rate = PaidFundingRate.select(
    #     fn.Sum(PaidFundingRate.amount)
    # ).where(PaidFundingRate.timestamp > from_time, PaidFundingRate.amount < 0).scalar() or Decimal(0)

    data.paid_funding_rate = BinanceIncome.select(fn.Sum(BinanceIncome.amount)).where(
        BinanceIncome.timestamp > from_time,
        BinanceIncome.amount < 0,
        BinanceIncome.type == "FUNDING_FEE",
        BinanceIncome.tenant == context.tenant,
    ).scalar() or Decimal(0)

    positions = context.utils.binance_client.futures_position_information()
    open_positions = [p for p in positions if Decimal(p["notional"]) != 0]

    next_funding_rate = defaultdict(lambda: Decimal(0))
    for pos in open_positions:
        notional, symbol, side = (
            Decimal(pos["notional"]),
            pos["symbol"],
            pos["positionSide"],
        )
        funding_rate = pos["fundingRate"] = real_time_funding_rate(symbol=symbol)
        funding_rate_fee = -1 * notional * funding_rate
        next_funding_rate[symbol] += funding_rate_fee * 10**18

    data.next_funding_rate = next_funding_rate

    data.timestamp = datetime.utcnow()
    aggregate_data = AggregateData.create(**data)
    return aggregate_data
