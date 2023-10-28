import json
from datetime import datetime, timedelta
from decimal import Decimal

import peewee
import requests
import web3
from multicallable import Multicallable
from peewee import fn

from app.models import (
    Account,
    AggregateData,
    DailyHistory,
    PaidFundingRate,
    Quote,
    Symbol,
    TradeHistory,
)
from config.local_settings import (
    deposit_diff,
    from_unix_timestamp,
    hedger_address,
    hedger_max_open_interest_ratio,
    rpc,
    symmio_abi,
    symmio_address,
    symmio_collateral_address,
    symmio_liquidators,
    symmio_multi_account,
)
from config.settings import erc20_abi, fetch_data_interval, funding_rate_alert_threshold
from context.context import binance_client
from cronjobs.binance_trade_volume import calculate_binance_trade_volume
from cronjobs.data_loaders import (
    load_accounts,
    load_daily_histories,
    load_quotes,
    load_symbols,
    load_trade_histories,
    load_users,
)
from cronjobs.state_indicator import StateIndicator, IndicatorMode
from utils.common_utils import load_config
from utils.formatter_utils import format
from utils.string_builder import StringBuilder
from utils.telegram_utils import send_message, escape_markdown_v1

quote_status_names = {
    0: "PENDING",
    1: "LOCKED",
    2: "CANCEL_PENDING",
    3: "CANCELED",
    4: "OPENED",
    5: "CLOSE_PENDING",
    6: "CANCEL_CLOSE_PENDING",
    7: "CLOSED",
    8: "LIQUIDATED",
    9: "EXPIRED",
}

from_time = datetime.fromtimestamp(from_unix_timestamp / 1000)


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def get_yesterday_last_aggregate():
    yesterday = datetime.utcnow() - timedelta(days=1)
    yesterday_end = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)

    return (
        AggregateData.select()
        .where(AggregateData.timestamp <= yesterday_end)
        .order_by(AggregateData.timestamp.desc())
        .get()
    )


def calculate_liquidator_states_diff(old_states, new_states):
    diff_states = []

    old_states_dict = {state["address"]: state for state in old_states}
    new_states_dict = {state["address"]: state for state in new_states}

    for address, new_state in new_states_dict.items():
        old_state = old_states_dict.get(address)
        if old_state:
            diff_state = {
                "address": address,
                "withdraw": new_state["withdraw"] - old_state["withdraw"],
                "balance": new_state["balance"] - old_state["balance"],
            }
        else:
            diff_state = new_state
        diff_states.append(diff_state)

    return diff_states


def calculate_status_quotes_diff(old_quotes, new_quotes):
    diff_quotes = {}

    for quote, new_value in new_quotes.items():
        old_value = old_quotes.get(quote)
        if old_value is not None:
            diff = new_value - old_value
        else:
            diff = new_value
        diff_quotes[quote] = diff

    return diff_quotes


def calculate_diff(old_data: AggregateData, new_data: AggregateData):
    diff_data = AggregateData()

    field_names = [
        field.name
        for field in AggregateData._meta.fields.values()
        if isinstance(field, peewee.DecimalField)
           or isinstance(field, peewee.IntegerField)
    ]

    for field_name in field_names:
        old_value = getattr(old_data, field_name)
        new_value = getattr(new_data, field_name)
        diff = new_value - old_value
        setattr(diff_data, field_name, diff)

    diff_data.timestamp = new_data.timestamp

    diff_data.status_quotes = calculate_status_quotes_diff(
        json.loads(old_data.status_quotes.replace("'", '"')), new_data.status_quotes
    )
    diff_data.liquidator_states = calculate_liquidator_states_diff(
        old_data.liquidator_states, new_data.liquidator_states
    )

    return diff_data


def real_time_funding_rate(symbol: str) -> Decimal:
    url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}"
    response = requests.get(url)
    funding_rate = Decimal(0)
    if response.status_code == 200:
        data = response.json()
        funding_rate = Decimal(data['lastFundingRate'])
    else:
        print("An error occurred:", response.status_code)
    return funding_rate


def calculate_aggregate_data(config):
    data = AttrDict()
    q_counts = (
        Quote.select(Quote.quoteStatus, fn.Count(Quote.id).alias("count"))
        .join(Account)
        .where(
            Quote.timestamp > from_time,
            Account.accountSource == symmio_multi_account,
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
            Account.accountSource == symmio_multi_account,
            Quote.partyB == hedger_address,
            Quote.quoteStatus == 7,
            Quote.timestamp > from_time,
        )
    )
    data.pnl_of_closed = Decimal(0)
    for quote in party_b_closed_quotes:
        if quote.positionType == "0":
            data.pnl_of_closed -= Decimal(
                int(quote.quantity)
                * (int(quote.avgClosedPrice) - int(quote.openPrice))
                / 10 ** 18
            )
        else:
            data.pnl_of_closed -= Decimal(
                int(quote.quantity)
                * (int(quote.openPrice) - int(quote.avgClosedPrice))
                / 10 ** 18
            )

    party_b_liquidated_quotes = (
        Quote.select()
        .join(Account)
        .where(
            Account.accountSource == symmio_multi_account,
            Quote.partyB == hedger_address,
            Quote.quoteStatus == 8,
            Quote.timestamp > from_time,
        )
    )
    data.pnl_of_liquidated = Decimal(0)
    for quote in party_b_liquidated_quotes:
        if quote.positionType == "0":
            data.pnl_of_liquidated -= Decimal(
                int(quote.quantity)
                * (int(quote.avgClosedPrice) - int(quote.openPrice))
                / 10 ** 18
            )
        else:
            data.pnl_of_liquidated -= Decimal(
                int(quote.quantity)
                * (int(quote.openPrice) - int(quote.avgClosedPrice))
                / 10 ** 18
            )

    # ------------------------------------------

    prices = binance_client.futures_mark_price()
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
            Account.accountSource == symmio_multi_account,
            Quote.timestamp > from_time,
            Quote.partyB == hedger_address,
            (
                    (Quote.quoteStatus == 4)
                    | (Quote.quoteStatus == 5)
                    | (Quote.quoteStatus == 6)
            ),
        )
    )

    subgraph_open_quotes = []
    data.hedger_upnl = Decimal(0)
    for quote in party_b_opened_quotes:
        key = f"{quote.id}-{quote.openPrice}-{quote.closedAmount}-{quote.quantity}"
        subgraph_open_quotes.append(key)
        side_sign = 1 if quote.positionType == "0" else -1
        current_price = Decimal(prices_map[quote.symbolId.name]) * 10 ** 18
        data.hedger_upnl += (
                side_sign
                * (quote.openPrice - current_price)
                * (quote.quantity - quote.closedAmount)
                // 10 ** 18
        )

    # ------------------------------------------

    closed_trade_histories = (
        TradeHistory.select()
        .join(Account)
        .where(
            Account.accountSource == symmio_multi_account,
            TradeHistory.quoteStatus == 7,
            TradeHistory.timestamp > from_time,
        )
    )
    data.closed_notional_value = sum(int(th.volume) for th in closed_trade_histories)

    liquidated_trade_histories = (
        TradeHistory.select()
        .join(Account)
        .where(
            Account.accountSource == symmio_multi_account,
            TradeHistory.quoteStatus == 8,
            TradeHistory.timestamp > from_time,
        )
    )
    data.liquidated_notional_value = sum(
        int(th.volume) for th in liquidated_trade_histories
    )

    opened_trade_histories = (
        TradeHistory.select()
        .join(Account)
        .where(
            Account.accountSource == symmio_multi_account,
            TradeHistory.quoteStatus == 4,
            TradeHistory.timestamp > from_time,
        )
    )
    data.opened_notional_value = sum(int(th.volume) for th in opened_trade_histories)

    # ------------------------------------------

    party_b_liquidated_party_a_quotes = (
        Quote.select()
        .join(Account)
        .where(
            Account.accountSource == symmio_multi_account,
            Quote.partyB == hedger_address,
            Quote.quoteStatus == 8,
            Quote.liquidatedSide == 0,
            Quote.timestamp > from_time,
        )
    )
    data.earned_cva = sum(int(q.cva) for q in party_b_liquidated_party_a_quotes)

    party_b_liquidated_party_b_quotes = (
        Quote.select()
        .join(Account)
        .where(
            Account.accountSource == symmio_multi_account,
            Quote.partyB == hedger_address,
            Quote.quoteStatus == 8,
            Quote.liquidatedSide == 1,
            Quote.timestamp > from_time,
        )
    )
    data.loss_cva = sum(int(q.cva) for q in party_b_liquidated_party_b_quotes)

    # ------------------------------------------

    w3 = web3.Web3(web3.Web3.HTTPProvider(rpc))
    contract_multicallable = Multicallable(
        w3.to_checksum_address(symmio_address), symmio_abi, w3
    )
    data.hedger_contract_balance = contract_multicallable.balanceOf(
        [w3.to_checksum_address(hedger_address)]
    ).call()[0]
    hedger_account = Account.get_by_id(hedger_address)
    data.hedger_contract_deposit = (
            int(hedger_account.deposit) * 10 ** (18 - config.decimals) - deposit_diff
    )
    data.hedger_contract_withdraw = int(hedger_account.withdraw) * 10 ** (
            18 - config.decimals
    )
    all_accounts = list(
        Account.select(Account.id).where(Account.accountSource == symmio_multi_account)
    )
    pages_count = len(all_accounts) // 100 if len(all_accounts) > 0 else 100
    hedger_addr = w3.to_checksum_address(hedger_address)
    data.hedger_contract_allocated = Decimal(
        sum(
            contract_multicallable.allocatedBalanceOfPartyB(
                [(hedger_addr, w3.to_checksum_address(a.id)) for a in all_accounts]
            ).call(n=pages_count)
        )
    )
    accounts = Account.select().where(Account.accountSource == symmio_multi_account)
    data.all_contract_deposit = sum(int(a.deposit) for a in accounts) * 10 ** (
            18 - config.decimals
    )
    data.all_contract_withdraw = sum(int(a.withdraw) for a in accounts) * 10 ** (
            18 - config.decimals
    )

    # Read contract balance of contract
    w3 = web3.Web3(web3.Web3.HTTPProvider(rpc))
    collateral_contract = w3.eth.contract(
        address=w3.to_checksum_address(symmio_collateral_address), abi=erc20_abi
    )
    data.contract_balance = collateral_contract.functions.balanceOf(
        w3.to_checksum_address(symmio_address)
    ).call()

    ppp = contract_multicallable.getPartyAOpenPositions(
        [(w3.to_checksum_address(a.id), 0, 100) for a in all_accounts]
    ).call(n=pages_count)

    print("Diff of open quotes with subgraph")
    for pp in ppp:
        for quote in pp:
            key = f"{quote[0]}-{quote[5]}-{quote[9]}-{quote[8]}"
            if key not in subgraph_open_quotes:
                db_quote = Quote.get_or_none(Quote.id == quote[0])
                if db_quote:
                    print(
                        f"{key}:{db_quote.id}-{db_quote.openPrice}-{db_quote.closedAmount}-{db_quote.quantity}"
                    )
                else:
                    print(f"Not found opened quote in subgraph: {key}")
    print("----------------------------------")

    # ------------------------------------------

    data.accounts_count = (
                              Account.select(fn.count(Account.id))
                              .where(Account.timestamp > from_time, Account.accountSource == symmio_multi_account)
                              .scalar()
                          ) or 0
    active_timestamp = datetime.utcnow() - timedelta(hours=48)
    data.active_accounts = (
                               Account.select(fn.count(Account.id))
                               .where(
                                   Account.accountSource == symmio_multi_account,
                                   Account.lastActivityTimestamp > active_timestamp,
                                   Account.timestamp > from_time,
                               )
                               .scalar()
                           ) or 0
    data.users_count = (
                           Account
                           .select(fn.COUNT(fn.DISTINCT(Account.user)))
                           .where(
                               Account.accountSource == symmio_multi_account,
                               Account.timestamp > from_time,
                           ).scalar()
                       ) or 0
    data.active_users = (
                            Account
                            .select(fn.COUNT(fn.DISTINCT(Account.user)))
                            .where(
                                Account.accountSource == symmio_multi_account,
                                Account.lastActivityTimestamp > active_timestamp,
                                Account.timestamp > from_time,
                            ).scalar()
                        ) or 0

    # ------------------------------------------

    for liquidator in symmio_liquidators:
        account = Account.get_or_none(Account.id == liquidator)
        if account is None:
            account = Account()
            account.withdraw = 0
        liquidator_state = {
            "address": liquidator,
            "withdraw": (int(account.withdraw) if account else 0)
                        * 10 ** (18 - config.decimals),
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
                                DailyHistory.accountSource == symmio_multi_account,
                            )
                            .scalar()
                        ) or 0

    data.trade_volume = (
                            DailyHistory.select(fn.Sum(DailyHistory.tradeVolume))
                            .where(
                                DailyHistory.timestamp > from_time,
                                DailyHistory.accountSource == symmio_multi_account,
                            )
                            .scalar()
                        ) or 0
    # ------------------------------------------

    binance_account = binance_client.futures_account(version=2)
    data.binance_maintenance_margin = Decimal(
        float(binance_account["totalMaintMargin"]) * 10 ** 18
    )
    data.binance_total_balance = Decimal(
        float(binance_account["totalMarginBalance"]) * 10 ** 18
    )
    data.binance_account_health_ratio = (
            100 - (data.binance_maintenance_margin / data.binance_total_balance) * 100
    )
    data.binance_cross_upnl = Decimal(binance_account["totalCrossUnPnl"]) * 10 ** 18
    data.binance_av_balance = Decimal(binance_account["availableBalance"]) * 10 ** 18
    data.binance_total_initial_margin = (
            Decimal(binance_account["totalInitialMargin"]) * 10 ** 18
    )
    data.binance_max_withdraw_amount = (
            Decimal(binance_account["maxWithdrawAmount"]) * 10 ** 18
    )
    data.max_open_interest = Decimal(
        hedger_max_open_interest_ratio * data.binance_max_withdraw_amount
    )
    data.binance_deposit = config.binanceDeposit
    data.binance_trade_volume = Decimal(calculate_binance_trade_volume() * 10 ** 18)

    # ------------------------------------------
    data.paid_funding_rate = PaidFundingRate.select(
        fn.Sum(PaidFundingRate.amount)
    ).where(PaidFundingRate.timestamp > from_time, PaidFundingRate.amount < 0).scalar() or Decimal(0)

    positions = binance_client.futures_position_information()
    open_positions = [p for p in positions if Decimal(p['notional']) != 0]

    total_funding_rate_fees = 0
    open_positions_fee = {}
    for pos in open_positions:
        notional, symbol, side = Decimal(pos['notional']), pos["symbol"], pos["positionSide"]
        funding_rate = pos['fundingRate'] = real_time_funding_rate(symbol=symbol)
        symbol_side = f'{symbol}-{"S" if side == "SHORT" else "L"}'
        funding_rate_fee = -1 * notional * funding_rate
        pos['fundingRateFee'] = open_positions_fee[symbol_side] = funding_rate_fee
        total_funding_rate_fees += funding_rate_fee

    data.next_funding_rate = total_funding_rate_fees * 10 ** 18

    data.timestamp = datetime.utcnow()
    aggregate_data = AggregateData.create(**data)
    return aggregate_data


def is_end_of_day():
    now = datetime.utcnow()
    end_of_day = datetime(
        now.year, now.month, now.day, 23, 59 - (fetch_data_interval // 60), 30
    )
    return now >= end_of_day


def fetch_data():
    config = load_config()
    current_time = datetime.utcnow() - timedelta(minutes=4)  # for subgraph sync time

    load_users(config)
    load_symbols(config)
    load_accounts(config)
    load_quotes(config)
    load_trade_histories(config)
    load_daily_histories(config)

    print("Data loaded...\nPreparing aggregate data...")
    aggregate_data = calculate_aggregate_data(config)

    config = load_config()  # Configuration may have changed during this method
    config.updateTimestamp = current_time
    config.upsert()

    end_day_tag = is_end_of_day()

    try:
        last_night_aggregate = get_yesterday_last_aggregate()
        diff_data = calculate_diff(
            old_data=last_night_aggregate, new_data=aggregate_data
        )
        report_aggregate_data(aggregate_data, diff_data, end_day_tag)
    except:
        # for testing !
        last_night_aggregate = (
            AggregateData.select().order_by(AggregateData.timestamp.asc()).get()
        )
        diff_data = calculate_diff(
            old_data=last_night_aggregate, new_data=aggregate_data
        )
        report_aggregate_data(aggregate_data, diff_data, end_day_tag)
        pass


def report_aggregate_data(
        data: AggregateData, today_data: AggregateData, end_dey_tag=False
):
    print("Reporting aggregate data...")
    sb = StringBuilder()

    indicators = []
    funding_indicator = StateIndicator("FundingRate")
    if data.next_funding_rate < -(funding_rate_alert_threshold * 10 ** 18):
        funding_indicator.set_mode(IndicatorMode.RED)
    else:
        funding_indicator.set_mode(IndicatorMode.GREEN)

    indicators.append(funding_indicator)

    mentions = set()
    for indicator in indicators:
        mentions.update(funding_indicator.get_mentions())
        sb.append(indicator.mode)

    sb.append_line()
    binance_deposit = int(data.binance_deposit) if data.binance_deposit else 0
    binance_profit = data.binance_total_balance - binance_deposit
    contract_profit = (
            data.hedger_contract_balance
            + data.hedger_contract_allocated
            + data.hedger_upnl
            - data.hedger_contract_deposit
            + data.hedger_contract_withdraw
    )
    total_state = binance_profit + contract_profit

    today_binance_deposit = (
        int(today_data.binance_deposit) if today_data.binance_deposit else 0
    )
    today_binance_profit = today_data.binance_total_balance - today_binance_deposit
    today_contract_profit = (
            today_data.hedger_contract_balance
            + today_data.hedger_contract_allocated
            + today_data.hedger_upnl
            - today_data.hedger_contract_deposit
            + today_data.hedger_contract_withdraw
    )
    today_total_state = today_binance_profit + today_contract_profit

    sb.append_line(f"Total State: {format(total_state)} | {format(today_total_state)}")
    sb.append_line(
        f"Total State - CVA: {format(total_state - data.earned_cva)} | {format(today_total_state - today_data.earned_cva)}"
    )
    sb.append_line(
        f"Binance Profit: {format(binance_profit)} | {format(today_binance_profit)}"
    )
    sb.append_line(
        f"Contract Profit: {format(contract_profit)} | {format(today_contract_profit)}"
    )

    sb.append_line(
        f"Platform Fee: {format(data.platform_fee)} | {format(today_data.platform_fee)}"
    )
    sb.append_line(
        f"Trade Volume: {format(data.trade_volume)} | {format(today_data.trade_volume)}"
    )
    sb.append_line("\n---- 💸 Funding Rate 💸 ----")
    sb.append_line(f"Next funding rate: {format(data.next_funding_rate)}")
    sb.append_line(
        f"Paid funding rate: {format(data.paid_funding_rate)} | {format(today_data.paid_funding_rate)}"
    )
    sb.append_line("\n---- 💰 Deposits Of Hedger 💰 ----")
    sb.append_line(
        f"Binance Deposit: {format(binance_deposit)} | {format(today_binance_deposit)}"
    )
    sb.append_line(
        f"Binance Balance: {format(data.binance_total_balance)} | {format(today_data.binance_total_balance)}"
    )
    sb.append_line("--------")
    sb.append_line(
        f"Contract Allocated: {format(data.hedger_contract_allocated)} | {format(today_data.hedger_contract_allocated)}"
    )
    sb.append_line(
        f"Contract Deposit: {format(data.hedger_contract_deposit)} | {format(today_data.hedger_contract_deposit)}"
    )
    sb.append_line(
        f"Contract Balance: {format(data.hedger_contract_balance)} | {format(today_data.hedger_contract_balance)}"
    )
    sb.append_line(
        f"Contract Withdraw: {format(data.hedger_contract_withdraw)} | {format(today_data.hedger_contract_withdraw)}"
    )

    sb.append_line("\n---- 📝 Quotes stats 📝 ----")
    for id, count in data.status_quotes.items():
        sb.append_line(
            f"{quote_status_names[int(id)]} : {count} | {today_data.status_quotes[id]}"
        )

    sb.append_line("\n---- 🧮 Hedger PNL 🧮 ----")
    sb.append_line(
        f"UPNL of hedger: {format(data.hedger_upnl)} | {format(today_data.hedger_upnl)}"
    )
    sb.append_line(
        f"PNL of closed quotes: {format(data.pnl_of_closed)} | {format(today_data.pnl_of_closed)}"
    )
    sb.append_line(
        f"PNL of liquidated quotes: {format(data.pnl_of_liquidated)} | {format(today_data.pnl_of_liquidated)}"
    )
    sb.append_line("\n---- 💰 Notional Value 💰 ----")
    sb.append_line(
        f"Closed Notional Value: {format(data.closed_notional_value)} | {format(today_data.closed_notional_value)}"
    )
    sb.append_line(
        f"Liquidated Notional Value: {format(data.liquidated_notional_value)} | {format(today_data.liquidated_notional_value)}"
    )
    sb.append_line(
        f"Opened Notional Value: {format(data.opened_notional_value)} | {format(today_data.opened_notional_value)}"
    )
    sb.append_line("\n---- ⚖️ Hedger CVA ⚖️ ----")
    sb.append_line(
        f"Earned CVA: {format(data.earned_cva)} | {format(today_data.earned_cva)}"
    )
    sb.append_line(f"Loss CVA: {format(data.loss_cva)} | {format(today_data.loss_cva)}")
    sb.append_line("\n---- 🏦 All Accounts Report 🏦 ----")
    sb.append_line(
        f"All Accounts Deposit: {format(data.all_contract_deposit)} | {format(today_data.all_contract_deposit)}"
    )
    sb.append_line(
        f"All Accounts Withdraw: {format(data.all_contract_withdraw)} | {format(today_data.all_contract_withdraw)}"
    )
    sb.append_line(
        f"Contract Balance: {format(data.contract_balance)} | {format(today_data.contract_balance)}"
    )
    sb.append_line("\n---- 👤 Users Report 👤 ----")
    sb.append_line(f"Accounts: {data.accounts_count} | {today_data.accounts_count}")
    sb.append_line(
        f"    active (48H): {data.active_accounts} | {today_data.active_accounts}"
    )
    sb.append_line(f"Users: {data.users_count} | {today_data.users_count}")
    sb.append_line(f"    active (48H): {data.active_users} | {today_data.active_users}")
    sb.append_line("\n---- 💸  Liquidators state 💸  ----")
    if data.liquidator_states:
        for ind, state in enumerate(data.liquidator_states):
            state2 = today_data.liquidator_states[ind]
            sb.append_line(f"{state['address']}")
            sb.append_line(
                f"    Withdraw: {format(state['withdraw'])} | {format(state2['withdraw'])}"
            )
            sb.append_line(
                f"    Current Balance: {format(state['balance'])} | {format(state2['balance'])}"
            )
            sb.append_line(
                f"    Current Allocated: {format(state['allocated'])} | {format(state2['allocated'] if 'allocated' in state2 else 0)}"
            )

    sb.append_line("\n---- 🟡 Binance Info 🟡 ----")
    sb.append_line(
        f"Maintenance Margin : {format(data.binance_maintenance_margin)} | {format(today_data.binance_maintenance_margin)}"
    )
    sb.append_line(
        f"Account Health Ratio : {format(data.binance_account_health_ratio, decimals=0)} | {format(today_data.binance_account_health_ratio, decimals=0)}"
    )
    sb.append_line(
        f"Cross UPNL : {format(data.binance_cross_upnl)} | {format(today_data.binance_cross_upnl)}"
    )
    sb.append_line(
        f"Available Balance : {format(data.binance_av_balance)} | {format(today_data.binance_av_balance)}"
    )
    sb.append_line(
        f"Total Initial Margin : {format(data.binance_total_initial_margin)} | {format(today_data.binance_total_initial_margin)}"
    )
    sb.append_line(
        f"Max Withdraw Amount : {format(data.binance_max_withdraw_amount)} | {format(today_data.binance_max_withdraw_amount)}"
    )
    sb.append_line(
        f"Total Trade Volume : {format(data.binance_trade_volume)} | {format(today_data.binance_trade_volume)}"
    )
    sb.append_line("---------------------")
    sb.append_line(
        f"Fetching data at {datetime.utcnow().strftime('%A, %d. %B %Y %I:%M:%S %p')} UTC"
    )
    if end_dey_tag:
        sb.append_line("#EndOfDay")

    send_message(escape_markdown_v1(str(sb)) + "\n" + ''.join(f'[.](tg://user?id={user})' for user in mentions))
    print("Reported....")
