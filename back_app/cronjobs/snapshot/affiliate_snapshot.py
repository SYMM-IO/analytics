from datetime import datetime, timedelta
from decimal import Decimal

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
)
from config.settings import (
    Context,
    SYMMIO_ABI,
    AffiliateContext,
)
from utils.attr_dict import AttrDict


def prepare_affiliate_snapshot(
    config, context: Context, affiliate_context: AffiliateContext
):
    from_time = datetime.fromtimestamp(context.from_unix_timestamp / 1000)
    hedger_context = context.hedger_for_affiliate(affiliate_context.name)
    snapshot = AttrDict()

    snapshot.status_quotes = count_quotes_per_status(
        affiliate_context, context, from_time
    )

    snapshot.pnl_of_closed = calculate_pnl_of_hedger(
        context, affiliate_context, hedger_context, 7, from_time
    )
    snapshot.pnl_of_liquidated = calculate_pnl_of_hedger(
        context, affiliate_context, hedger_context, 8, from_time
    )

    snapshot.hedger_upnl, subgraph_open_quotes = calculate_hedger_upnl(
        context, affiliate_context, hedger_context, from_time
    )

    snapshot.closed_notional_value = calculate_notional_value(
        context, affiliate_context, 7, from_time
    )
    snapshot.liquidated_notional_value = calculate_notional_value(
        context, affiliate_context, 8, from_time
    )
    snapshot.opened_notional_value = calculate_notional_value(
        context, affiliate_context, 4, from_time
    )
    # ------------------------------------------

    party_b_liquidated_party_a_quotes = (
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
    snapshot.earned_cva = sum(int(q.cva) for q in party_b_liquidated_party_a_quotes)

    party_b_liquidated_party_b_quotes = (
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
    snapshot.loss_cva = sum(int(q.cva) for q in party_b_liquidated_party_b_quotes)

    # ------------------------------------------
    w3 = web3.Web3(web3.Web3.HTTPProvider(context.rpc))
    contract_multicallable = Multicallable(
        w3.to_checksum_address(context.symmio_address), SYMMIO_ABI, w3
    )
    all_accounts = list(
        Account.select(Account.id).where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            Account.tenant == context.tenant,
        )
    )
    pages_count = len(all_accounts) // 100 if len(all_accounts) > 100 else 1
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
            # key = f"{quote.id}-{quote.openPrice}-{quote.closedAmount}-{quote.quantity}"
            key = f"{context.tenant}_{quote[0]}-{quote[5]}-{quote[10]}-{quote[9]}"
            quote_id = f"{context.tenant}_{quote[0]}"
            if key not in subgraph_open_quotes:
                db_quote = Quote.get_or_none(
                    Quote.id == quote_id, Quote.tenant == context.tenant
                )
                if db_quote:
                    print(
                        f"{context.tenant} => Contract: {key} Local DB: {db_quote.id}-{db_quote.openPrice}-{db_quote.closedAmount}-{db_quote.quantity}"
                    )
                else:
                    print(
                        f"{context.tenant} => Contract opened quote not found in the subgraph: {key}"
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


def calculate_notional_value(context, affiliate_context, quote_status, from_time):
    closed_trade_histories = (
        TradeHistory.select()
        .join(Account)
        .where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            TradeHistory.quoteStatus == quote_status,
            TradeHistory.timestamp > from_time,
            TradeHistory.tenant == context.tenant,
        )
    )
    return sum(int(th.volume) for th in closed_trade_histories)


def calculate_hedger_upnl(context, affiliate_context, hedger_context, from_time):
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
    hedger_upnl = Decimal(0)
    for quote in party_b_opened_quotes:
        key = f"{quote.id}-{quote.openPrice}-{quote.closedAmount}-{quote.quantity}"
        subgraph_open_quotes.append(key)
        side_sign = 1 if quote.positionType == "0" else -1
        current_price = Decimal(prices_map[quote.symbolId.name]) * 10**18
        hedger_upnl += (
            side_sign
            * (quote.openPrice - current_price)
            * (quote.quantity - quote.closedAmount)
            // 10**18
        )
    return hedger_upnl, subgraph_open_quotes


def calculate_pnl_of_hedger(
    context, affiliate_context, hedger_context, quote_status, from_time
):
    party_b_quotes = (
        Quote.select()
        .join(Account)
        .where(
            Account.accountSource == affiliate_context.symmio_multi_account,
            Quote.partyB == hedger_context.hedger_address,
            Quote.quoteStatus == quote_status,
            Quote.timestamp > from_time,
            Quote.tenant == context.tenant,
        )
    )
    pnl = Decimal(0)
    for quote in party_b_quotes:
        if quote.positionType == "0":
            pnl -= Decimal(
                int(quote.quantity)
                * (int(quote.avgClosedPrice) - int(quote.openPrice))
                / 10**18
            )
        else:
            pnl -= Decimal(
                int(quote.quantity)
                * (int(quote.openPrice) - int(quote.avgClosedPrice))
                / 10**18
            )
    return pnl


def count_quotes_per_status(affiliate_context, context, from_time):
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
    return status_quotes
