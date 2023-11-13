import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

import peewee

from app.models import AggregateData, StatsBotMessage
from config.local_settings import main_market_symbols
from config.settings import funding_rate_alert_threshold, fetch_data_interval, closable_funding_rate_alert_threshold
from cronjobs.bot.indicators.mismatch_indicator import MismatchIndicator, FieldCheck
from cronjobs.bot.indicators.state_indicator import StateIndicator, IndicatorMode
from utils.common_utils import load_config
from utils.formatter_utils import format
from utils.parser_utils import parse_message
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


def is_end_of_day():
    now = datetime.utcnow()
    end_of_day = datetime(
        now.year, now.month, now.day, 23, 59 - (fetch_data_interval // 60), 30
    )
    return now >= end_of_day


def prepare_and_report_data(aggregate_data: AggregateData):
    messages = StatsBotMessage.select().order_by(StatsBotMessage.id.desc()).limit(1).execute()
    if len(messages) == 0:
        return
    last_msg = messages[0]
    parsed_message = parse_message(last_msg.content)

    config = load_config()
    config.binanceDeposit = Decimal(parsed_message["binance deposited"] * 10 ** 18)
    config.save()

    aggregate_data.binance_deposit = config.binanceDeposit
    aggregate_data.save()

    end_day_tag = is_end_of_day()
    try:
        last_night_aggregate = get_yesterday_last_aggregate()
        diff_data = calculate_diff(
            old_data=last_night_aggregate, new_data=aggregate_data
        )
        report_aggregate_data(aggregate_data, diff_data, parsed_message, end_day_tag)
    except:
        # for testing !
        last_night_aggregate = (
            AggregateData.select().order_by(AggregateData.timestamp.asc()).get()
        )
        diff_data = calculate_diff(
            old_data=last_night_aggregate, new_data=aggregate_data
        )
        report_aggregate_data(aggregate_data, diff_data, parsed_message, end_day_tag)
        pass


FUNDING_RATE_THRESHOLD = -(funding_rate_alert_threshold * 10 ** 18)
CLOSABLE_FUNDING_RATE_THRESHOLD = -(closable_funding_rate_alert_threshold * 10 ** 18)


def initialize_indicators(data: AggregateData, parsed_stat_message: dict) -> List[StateIndicator]:
    non_closable_funding = 0
    for market, value in data.next_funding_rate.items():
        if market in main_market_symbols:
            non_closable_funding += value

    non_closable_funding_indicator = StateIndicator(
        "FundingRate", mode=IndicatorMode.RED
        if non_closable_funding < FUNDING_RATE_THRESHOLD
        else IndicatorMode.GREEN
    )

    closable_market_with_high_funding = None
    for market, value in data.next_funding_rate.items():
        if market not in main_market_symbols and value > CLOSABLE_FUNDING_RATE_THRESHOLD:
            closable_market_with_high_funding = market
            break

    closable_funding_indicator = StateIndicator(
        "ClosableFundingRate", mode=IndicatorMode.RED
        if closable_market_with_high_funding is not None
        else IndicatorMode.GREEN
    )

    mismatch_indicator = MismatchIndicator("MisMatch")
    mismatch_indicator.update_state(data, parsed_stat_message, [
        FieldCheck("total_state", "total state", 5)
    ])

    return [non_closable_funding_indicator, closable_funding_indicator, mismatch_indicator]


def report_aggregate_data(
        data: AggregateData, today_data: AggregateData, parsed_stat_message: dict, end_dey_tag=False
):
    print("Reporting aggregate data...")

    indicators = initialize_indicators(data, parsed_stat_message)
    mentions = set()
    for indicator in indicators:
        mentions.update(indicator.get_mentions())

    quote_stats_lines = [
        f"{quote_status_names[int(id)]} : {count} | {today_data.status_quotes[id]}"
        for id, count in data.status_quotes.items()
    ]
    quote_stats_info = "\n".join(quote_stats_lines)

    liquidators_state_info = "\n---- 💸 Liquidators state 💸 ----\n"
    if data.liquidator_states:
        for ind, state in enumerate(data.liquidator_states):
            state2 = today_data.liquidator_states[ind]
            liquidators_state_info += (
                f"{state['address']}\n"
                f"    Withdraw: {format(state['withdraw'])} | {format(state2['withdraw'])}\n"
                f"    Current Balance: {format(state['balance'])} | {format(state2['balance'])}\n"
                f"    Current Allocated: {format(state['allocated'])} | {format(state2.get('allocated', 0))}\n"
            )

    non_closable_funding = 0
    closable_funding = 0
    for market, value in data.next_funding_rate.items():
        if market in main_market_symbols:
            non_closable_funding += value
        else:
            closable_funding += value

    report = f"""
{"".join(indicator.mode for indicator in indicators)}

Total State: {format(data.total_state)} | {format(today_data.total_state)}
Total State - CVA: {format(data.total_state - data.earned_cva)} | {format(today_data.total_state - today_data.earned_cva)}
Binance Profit: {format(data.binance_profit)} | {format(today_data.binance_profit)}
Contract Profit: {format(data.contract_profit)} | {format(today_data.contract_profit)}

Platform Fee: {format(data.platform_fee)} | {format(today_data.platform_fee)}
Trade Volume: {format(data.trade_volume)} | {format(today_data.trade_volume)}

---- 💸 Funding Rate 💸 ----
Next funding rate non-closable: {format(non_closable_funding)}
Next funding rate closable: {format(closable_funding)}
Next funding rate total: {format(closable_funding + non_closable_funding)}
Paid funding rate: {format(data.paid_funding_rate)} | {format(today_data.paid_funding_rate)}

---- 💰 Deposits Of Hedger 💰 ----
Binance Deposit: {format(data.binance_deposit)} | {format(today_data.binance_deposit)}
Binance Balance: {format(data.binance_total_balance)} | {format(today_data.binance_total_balance)}

Contract Allocated: {format(data.hedger_contract_allocated)} | {format(today_data.hedger_contract_allocated)}
Contract Deposit: {format(data.hedger_contract_deposit)} | {format(today_data.hedger_contract_deposit)}
Contract Balance: {format(data.hedger_contract_balance)} | {format(today_data.hedger_contract_balance)}
Contract Withdraw: {format(data.hedger_contract_withdraw)} | {format(today_data.hedger_contract_withdraw)}

---- 📝 Quotes stats 📝 ----
{quote_stats_info}

---- 🧮 Hedger PNL 🧮 ----
UPNL of hedger: {format(data.hedger_upnl)} | {format(today_data.hedger_upnl)}
PNL of closed quotes: {format(data.pnl_of_closed)} | {format(today_data.pnl_of_closed)}
PNL of liquidated quotes: {format(data.pnl_of_liquidated)} | {format(today_data.pnl_of_liquidated)}

---- 💰 Notional Value 💰 ----
Closed Notional Value: {format(data.closed_notional_value)} | {format(today_data.closed_notional_value)}
Liquidated Notional Value: {format(data.liquidated_notional_value)} | {format(today_data.liquidated_notional_value)}
Opened Notional Value: {format(data.opened_notional_value)} | {format(today_data.opened_notional_value)}

---- ⚖️ Hedger CVA ⚖️ ----
Earned CVA: {format(data.earned_cva)} | {format(today_data.earned_cva)}
Loss CVA: {format(data.loss_cva)} | {format(today_data.loss_cva)}

---- 🏦 All Accounts Report 🏦 ----
All Accounts Deposit: {format(data.all_contract_deposit)} | {format(today_data.all_contract_deposit)}
All Accounts Withdraw: {format(data.all_contract_withdraw)} | {format(today_data.all_contract_withdraw)}
Contract Balance: {format(data.contract_balance)} | {format(today_data.contract_balance)}

---- 👤 Users Report 👤 ----
Accounts: {data.accounts_count} | {today_data.accounts_count}
    active (48H): {data.active_accounts} | {today_data.active_accounts}
Users: {data.users_count} | {today_data.users_count}
    active (48H): {data.active_users} | {today_data.active_users}

---- 🟡 Binance Info 🟡 ----
Maintenance Margin: {format(data.binance_maintenance_margin)} | {format(today_data.binance_maintenance_margin)}
Account Health Ratio: {format(data.binance_account_health_ratio, decimals=0)} | {format(today_data.binance_account_health_ratio, decimals=0)}
Cross UPNL: {format(data.binance_cross_upnl)} | {format(today_data.binance_cross_upnl)}
Available Balance: {format(data.binance_av_balance)} | {format(today_data.binance_av_balance)}
Total Initial Margin: {format(data.binance_total_initial_margin)} | {format(today_data.binance_total_initial_margin)}
Max Withdraw Amount: {format(data.binance_max_withdraw_amount)} | {format(today_data.binance_max_withdraw_amount)}
Total Trade Volume: {format(data.binance_trade_volume)} | {format(today_data.binance_trade_volume)}
{liquidators_state_info}
Fetching data at {datetime.utcnow().strftime('%A, %d. %B %Y %I:%M:%S %p')} UTC
"""
    if end_dey_tag:
        report += "#EndOfDay\n"

    send_message(escape_markdown_v1(report) + "\n" + ''.join(f'[.](tg://user?id={user})' for user in mentions))
    print("Reported....")
