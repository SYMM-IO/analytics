import json
from datetime import datetime, timedelta

import peewee

from app.models import AggregateData
from config.settings import funding_rate_alert_threshold, fetch_data_interval, closable_funding_rate_alert_threshold
from cronjobs.state_indicator import StateIndicator, IndicatorMode
from utils.string_builder import StringBuilder
from utils.telegram_utils import send_message, escape_markdown_v1
from utils.formatter_utils import format

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
    if data.next_funding_rate_total < -(funding_rate_alert_threshold * 10 ** 18):
        funding_indicator.set_mode(IndicatorMode.RED)
    else:
        funding_indicator.set_mode(IndicatorMode.GREEN)

    indicators.append(funding_indicator)

    closable_funding_indicator = StateIndicator("ClosableFundingRate")
    if data.next_funding_rate_total - data.next_funding_rate_main_markets < -(closable_funding_rate_alert_threshold * 10 ** 18):
        closable_funding_indicator.set_mode(IndicatorMode.RED)
    else:
        closable_funding_indicator.set_mode(IndicatorMode.GREEN)

    indicators.append(closable_funding_indicator)

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
    sb.append_line(f"Next funding rate total: {format(data.next_funding_rate_total)}")
    sb.append_line(f"Next funding rate main markets: {format(data.next_funding_rate_main_markets)}")
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
