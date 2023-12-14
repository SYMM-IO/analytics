from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import List

from app.models import AffiliateSnapshot, StatsBotMessage, HedgerSnapshot
from config.settings import (
    main_market_symbols,
    funding_rate_alert_threshold,
    closable_funding_rate_alert_threshold,
    Context,
)
from cronjobs.bot.indicators.mismatch_indicator import MismatchIndicator, FieldCheck
from cronjobs.bot.indicators.state_indicator import StateIndicator, IndicatorMode
from cronjobs.bot.utils import (
    is_end_of_day,
    get_yesterday_last_hedger_snapshot,
    calculate_hedger_snapshot_diff,
    get_yesterday_last_affiliate_snapshot,
    calculate_affiliates_snapshot_diff,
)
from cronjobs.snapshot_job import real_time_funding_rate
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

FUNDING_RATE_THRESHOLD = -(funding_rate_alert_threshold * 10**18)
CLOSABLE_FUNDING_RATE_THRESHOLD = -(closable_funding_rate_alert_threshold * 10**18)


def get_hedger_indicators(
    hedger_snapshot: HedgerSnapshot, parsed_stat_message: dict
) -> List[StateIndicator]:
    non_closable_funding = 0
    for market, value in hedger_snapshot.next_funding_rate.items():
        if market in main_market_symbols:
            non_closable_funding += value

    non_closable_funding_indicator = StateIndicator(
        "NonClosableFundingRate",
        mode=IndicatorMode.RED
        if non_closable_funding < FUNDING_RATE_THRESHOLD
        else IndicatorMode.GREEN,
    )

    closable_market_with_high_funding = None
    for market, value in hedger_snapshot.next_funding_rate.items():
        if (
            market not in main_market_symbols
            and value < CLOSABLE_FUNDING_RATE_THRESHOLD
        ):
            closable_market_with_high_funding = market
            break

    closable_funding_indicator = StateIndicator(
        "ClosableFundingRate",
        mode=IndicatorMode.RED
        if closable_market_with_high_funding is not None
        else IndicatorMode.GREEN,
    )

    mismatch_indicator = MismatchIndicator("MisMatch")
    mismatch_indicator.update_state(
        hedger_snapshot,
        parsed_stat_message,
        [FieldCheck("total_state", "total state", 5)],
    )

    return [
        non_closable_funding_indicator,
        closable_funding_indicator,
        mismatch_indicator,
    ]


def report_snapshots_to_telegram(context: Context):
    affiliates_snapshots = (
        AffiliateSnapshot.select()
        .where(AffiliateSnapshot.tenant == context.tenant)
        .order_by(AffiliateSnapshot.timestamp.desc())
        .limit(len(context.affiliates))
        .execute()
    )
    if len(affiliates_snapshots) < len(context.affiliates):
        return

    assert len(set([snapshot.name for snapshot in affiliates_snapshots])) == len(
        context.affiliates
    )

    hedger_snapshots = (
        HedgerSnapshot.select()
        .where(HedgerSnapshot.tenant == context.tenant)
        .order_by(HedgerSnapshot.timestamp.desc())
        .limit(len(context.hedgers))
        .execute()
    )

    if len(hedger_snapshots) < len(context.hedgers):
        return

    assert len(set([snapshot.name for snapshot in hedger_snapshots])) == len(
        context.hedgers
    )

    messages = (
        StatsBotMessage.select()
        .where(StatsBotMessage.tenant == context.tenant)
        .order_by(StatsBotMessage.message_id.desc())
        .limit(1)
        .execute()
    )
    if len(messages) == 0:
        return
    last_msg = messages[0]
    parsed_message = parse_message(last_msg.content)

    indicators = []
    hedger_messages = []
    affiliates_messages = []
    for hedger_snapshot in hedger_snapshots:
        related_affiliate_snapshots = [
            af for af in affiliates_snapshots if af.hedger_name == hedger_snapshot.name
        ]
        msg, indis = prepare_hedger_snapshot_message(
            context, hedger_snapshot, related_affiliate_snapshots, parsed_message
        )
        hedger_messages.append(msg)
        indicators.append(indis)

    for affiliates_snapshot in affiliates_snapshots:
        msg, indis = prepare_affiliate_snapshot_message(affiliates_snapshot)
        affiliates_messages.append(msg)
        indicators.append(indis)

    report = "".join(indicator.mode for indicator in indicators)
    report += "\n".join(hedger_messages)
    report += "\n".join(affiliates_messages)
    report += f"Fetching data at {datetime.utcnow().strftime('%A, %d. %B %Y %I:%M:%S %p')} UTC"
    if is_end_of_day():
        report += "#EndOfDay\n"

    mentions = set()
    for indicator in indicators:
        mentions.update(indicator.get_mentions())

    print(report)
    send_message(
        context,
        escape_markdown_v1(report)
        + "\n"
        + "".join(f"[.](tg://user?id={user})" for user in mentions),
    )
    print(f"{context.tenant}: Reported....")


def prepare_hedger_snapshot_message(
    context: Context,
    hedger_snapshot: HedgerSnapshot,
    affiliate_snapshots: List[AffiliateSnapshot],
    parsed_stat_message,
) -> (str, List[StateIndicator]):
    last_day_snapshot = get_yesterday_last_hedger_snapshot(hedger_snapshot)
    snapshot_diff = calculate_hedger_snapshot_diff(last_day_snapshot, hedger_snapshot)

    last_day_affiliates = [
        get_yesterday_last_affiliate_snapshot(af) for af in affiliate_snapshots
    ]
    affiliate_snapshots_diff = [
        calculate_affiliates_snapshot_diff(af_old, af_new)
        for af_new, af_old in zip(affiliate_snapshots, last_day_affiliates)
    ]

    positions = context.hedger_with_name(
        hedger_snapshot.name
    ).utils.binance_client.futures_position_information()
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

    hedger_snapshot.next_funding_rate = next_funding_rate

    non_closable_funding = 0
    closable_funding = 0
    for market, value in hedger_snapshot.next_funding_rate.items():
        if market in main_market_symbols:
            non_closable_funding += value
        else:
            closable_funding += value

    msg = f"""
\n--- ⚖️ {hedger_snapshot.name} ⚖️ ---\n
Total State: {format(hedger_snapshot.total_state(affiliate_snapshots))} | {format(snapshot_diff.total_state(affiliate_snapshots_diff))}
Total State - CVA: {format(hedger_snapshot.total_state(affiliate_snapshots) - HedgerSnapshot.earned_cva(affiliate_snapshots))} | {format(snapshot_diff.total_state(affiliate_snapshots_diff) - HedgerSnapshot.earned_cva(affiliate_snapshots_diff))}
Binance Profit: {format(hedger_snapshot.binance_profit)} | {format(snapshot_diff.binance_profit)}
Contract Profit: {format(hedger_snapshot.contract_profit(affiliate_snapshots))} | {format(snapshot_diff.contract_profit(affiliate_snapshots_diff))}

Binance Deposit: {format(hedger_snapshot.binance_deposit)} | {format(snapshot_diff.binance_deposit)}
Binance Balance: {format(hedger_snapshot.binance_total_balance)} | {format(snapshot_diff.binance_total_balance)}
Contract Deposit: {format(hedger_snapshot.hedger_contract_deposit)} | {format(snapshot_diff.hedger_contract_deposit)}
Contract Balance: {format(hedger_snapshot.hedger_contract_balance)} | {format(snapshot_diff.hedger_contract_balance)}
Contract Withdraw: {format(hedger_snapshot.hedger_contract_withdraw)} | {format(snapshot_diff.hedger_contract_withdraw)}

--- 💸 Funding Rate 💸 ---
Next funding rate non-closable: {format(non_closable_funding)}
Next funding rate closable: {format(closable_funding)}
Next funding rate total: {format(closable_funding + non_closable_funding)}
Paid funding rate: {format(hedger_snapshot.paid_funding_rate)} | {format(snapshot_diff.paid_funding_rate)}

--- 💰 Binance Info 💰 ---
Maintenance Margin: {format(hedger_snapshot.binance_maintenance_margin)} | {format(snapshot_diff.binance_maintenance_margin)}
Account Health Ratio: {format(hedger_snapshot.binance_account_health_ratio, decimals=0)} | {format(snapshot_diff.binance_account_health_ratio, decimals=0)}
Cross UPNL: {format(hedger_snapshot.binance_cross_upnl)} | {format(snapshot_diff.binance_cross_upnl)}
Available Balance: {format(hedger_snapshot.binance_av_balance)} | {format(snapshot_diff.binance_av_balance)}
Total Initial Margin: {format(hedger_snapshot.binance_total_initial_margin)} | {format(snapshot_diff.binance_total_initial_margin)}
Max Withdraw Amount: {format(hedger_snapshot.binance_max_withdraw_amount)} | {format(snapshot_diff.binance_max_withdraw_amount)}
Total Trade Volume: {format(hedger_snapshot.binance_trade_volume)} | {format(snapshot_diff.binance_trade_volume)}
    """
    return msg, get_hedger_indicators(hedger_snapshot, parsed_stat_message)


def prepare_affiliate_snapshot_message(
    affiliate_snapshot: AffiliateSnapshot,
) -> (str, List[StateIndicator]):
    last_day_snapshot = get_yesterday_last_affiliate_snapshot(affiliate_snapshot)
    snapshot_diff = calculate_affiliates_snapshot_diff(
        last_day_snapshot, affiliate_snapshot
    )

    quote_stats_lines = [
        f"{quote_status_names[int(id)]} : {count} | {snapshot_diff.status_quotes[id]}"
        for id, count in affiliate_snapshot.status_quotes.items()
    ]
    quote_stats_info = "\n".join(quote_stats_lines)

    liquidators_state_info = "\n---- 💸 Liquidators state 💸 ----\n"
    if affiliate_snapshot.liquidator_states:
        for ind, state in enumerate(affiliate_snapshot.liquidator_states):
            state2 = snapshot_diff.liquidator_states[ind]
            liquidators_state_info += (
                f"{state['address']}\n"
                f"    Withdraw: {format(state['withdraw'])} | {format(state2['withdraw'])}\n"
                f"    Current Balance: {format(state['balance'])} | {format(state2['balance'])}\n"
                f"    Current Allocated: {format(state['allocated'])} | {format(state2.get('allocated', 0))}\n"
            )

    msg = f"""
\n--- 🤝 {affiliate_snapshot.name} 🤝 ---\n
Allocated of hedger: {format(affiliate_snapshot.hedger_contract_allocated)} | {format(snapshot_diff.hedger_contract_allocated)}
Platform Fee: {format(affiliate_snapshot.platform_fee)} | {format(snapshot_diff.platform_fee)}
Trade Volume: {format(affiliate_snapshot.trade_volume)} | {format(snapshot_diff.trade_volume)}
--- 🧮 Hedger PNL 🧮 ---
UPNL of hedger: {format(affiliate_snapshot.hedger_upnl)} | {format(snapshot_diff.hedger_upnl)}
PNL of closed quotes: {format(affiliate_snapshot.pnl_of_closed)} | {format(snapshot_diff.pnl_of_closed)}
PNL of liquidated quotes: {format(affiliate_snapshot.pnl_of_liquidated)} | {format(snapshot_diff.pnl_of_liquidated)}
--- 📊 Notional Value 📊 ---
Closed Notional Value: {format(affiliate_snapshot.closed_notional_value)} | {format(snapshot_diff.closed_notional_value)}
Liquidated Notional Value: {format(affiliate_snapshot.liquidated_notional_value)} | {format(snapshot_diff.liquidated_notional_value)}
Opened Notional Value: {format(affiliate_snapshot.opened_notional_value)} | {format(snapshot_diff.opened_notional_value)}
--- 🏦 All Accounts Report 🏦 ---
All Accounts Deposit: {format(affiliate_snapshot.all_contract_deposit)} | {format(snapshot_diff.all_contract_deposit)}
All Accounts Withdraw: {format(affiliate_snapshot.all_contract_withdraw)} | {format(snapshot_diff.all_contract_withdraw)}
--- 👤 Users Report 👤 ---
Accounts: {affiliate_snapshot.accounts_count} | {snapshot_diff.accounts_count}
    active (48H): {affiliate_snapshot.active_accounts} | {snapshot_diff.active_accounts}
Users: {affiliate_snapshot.users_count} | {snapshot_diff.users_count}
    active (48H): {affiliate_snapshot.active_users} | {snapshot_diff.active_users}
--- ⚖️ Hedger CVA ⚖️ ---
Earned CVA: {format(affiliate_snapshot.earned_cva)} | {format(snapshot_diff.earned_cva)}
Loss CVA: {format(affiliate_snapshot.loss_cva)} | {format(snapshot_diff.loss_cva)}
--- 📝 Quotes stats 📝 ---
{quote_stats_info}
{liquidators_state_info}
    """
    return msg, []
