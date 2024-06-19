import json
from datetime import datetime, timedelta
from decimal import Decimal

from multicallable import Multicallable
from sqlalchemy import func, and_, or_, select
from sqlalchemy.orm import Session, load_only, joinedload

from app.models import (
    Account,
    AffiliateSnapshot,
    DailyHistory,
    Quote,
    Symbol,
    TradeHistory,
    BalanceChange,
    BalanceChangeType,
    RuntimeConfiguration,
)
from config.settings import (
    SYMMIO_ABI,
    AffiliateContext,
    HedgerContext,
    Context,
    DEBUG_MODE,
)
from cronjobs.snapshot.snapshot_context import SnapshotContext
from utils.attr_dict import AttrDict
from utils.block import Block


def prepare_affiliate_snapshot(
    snapshot_context: SnapshotContext,
    affiliate_context: AffiliateContext,
    hedger_context: HedgerContext,
    block: Block,
):
    print(f"----------------Prepare Affiliate Snapshot Of {hedger_context.name} -> {affiliate_context.name}")
    context: Context = snapshot_context.context
    session: Session = snapshot_context.session
    config: RuntimeConfiguration = snapshot_context.config

    from_time = datetime.fromtimestamp(context.from_unix_timestamp / 1000)
    snapshot = AttrDict()

    snapshot.status_quotes = json.dumps(count_quotes_per_status(session, affiliate_context, hedger_context, context, from_time, block))
    snapshot.pnl_of_closed = calculate_pnl_of_hedger(context, session, affiliate_context, hedger_context, 7, from_time, block)
    snapshot.pnl_of_liquidated = calculate_pnl_of_hedger(context, session, affiliate_context, hedger_context, 8, from_time, block)
    snapshot.hedger_upnl, subgraph_open_quotes = calculate_hedger_upnl(context, session, affiliate_context, hedger_context, from_time, block)
    snapshot.closed_notional_value = calculate_notional_value(context, session, affiliate_context, hedger_context, 7, from_time, block)
    snapshot.liquidated_notional_value = calculate_notional_value(context, session, affiliate_context, hedger_context, 8, from_time, block)
    snapshot.opened_notional_value = calculate_notional_value(context, session, affiliate_context, hedger_context, 4, from_time, block)
    # ------------------------------------------
    snapshot.earned_cva = Decimal(
        session.scalar(
            select(func.sum(Quote.cva))
            .join(Account)
            .where(
                and_(
                    Account.accountSource == affiliate_context.symmio_multi_account,
                    Quote.partyB == hedger_context.hedger_address,
                    Quote.quoteStatus == 8,
                    Quote.liquidatedSide == 1,
                    Quote.timestamp > from_time,
                    Quote.blockNumber <= block.number,
                    Quote.tenant == context.tenant,
                )
            )
        )
        or 0
    )

    snapshot.loss_cva = Decimal(
        session.scalar(
            select(func.sum(Quote.cva))
            .join(Account)
            .where(
                and_(
                    Account.accountSource == affiliate_context.symmio_multi_account,
                    Quote.partyB == hedger_context.hedger_address,
                    Quote.quoteStatus == 8,
                    Quote.liquidatedSide == 0,
                    Quote.timestamp > from_time,
                    Quote.blockNumber <= block.number,
                    Quote.tenant == context.tenant,
                )
            )
        )
        or 0
    )

    # ------------------------------------------
    contract_multicallable = Multicallable(snapshot_context.w3.to_checksum_address(context.symmio_address), SYMMIO_ABI, snapshot_context.w3)
    all_accounts = session.execute(
        select(Account.id).where(
            and_(
                Account.accountSource == affiliate_context.symmio_multi_account,
                Account.blockNumber <= block.number,
                Account.tenant == context.tenant,
            )
        )
    ).all()

    pages_count = len(all_accounts) // 100 if len(all_accounts) > 100 else 1
    hedger_addr = snapshot_context.w3.to_checksum_address(hedger_context.hedger_address)
    snapshot.hedger_contract_allocated = Decimal(
        sum(
            contract_multicallable.allocatedBalanceOfPartyB(
                [(hedger_addr, snapshot_context.w3.to_checksum_address(a.id)) for a in all_accounts]
            ).call(n=pages_count, block_identifier=block.number)
        )
    )

    all_accounts_deposit = Decimal(
        session.scalar(
            select(func.sum(BalanceChange.amount))
            .join(Account)
            .where(
                and_(
                    Account.accountSource == affiliate_context.symmio_multi_account,
                    BalanceChange.blockNumber <= block.number,
                    BalanceChange.type == BalanceChangeType.DEPOSIT,
                    BalanceChange.collateral == context.symmio_collateral_address,
                    BalanceChange.tenant == context.tenant,
                )
            )
        )
        or 0
    )
    snapshot.all_contract_deposit = all_accounts_deposit * 10 ** (18 - config.decimals)

    all_accounts_withdraw = Decimal(
        session.scalar(
            select(func.sum(BalanceChange.amount))
            .join(Account)
            .where(
                and_(
                    Account.accountSource == affiliate_context.symmio_multi_account,
                    BalanceChange.blockNumber <= block.number,
                    BalanceChange.type == BalanceChangeType.WITHDRAW,
                    BalanceChange.collateral == context.symmio_collateral_address,
                    BalanceChange.tenant == context.tenant,
                )
            )
        )
        or 0
    )
    snapshot.all_contract_withdraw = all_accounts_withdraw * 10 ** (18 - config.decimals)

    if DEBUG_MODE:
        ppp = contract_multicallable.getPartyAOpenPositions([(snapshot_context.w3.to_checksum_address(a.id), 0, 100) for a in all_accounts]).call(
            n=pages_count, block_identifier=block.number
        )

        print(f"{context.tenant}: Checking diff of open quotes with subgraph")
        for pp in ppp:
            for quote in pp:
                # key = f"{quote.id}-{9uiui8iuu jm  quote.openPrice}-{quote.closedAmount}-{quote.quantity}"
                key = f"{context.tenant}_{quote[0]}-{quote[5]}-{quote[10]}-{quote[9]}"
                quote_id = f"{context.tenant}_{quote[0]}"
                if key not in subgraph_open_quotes:
                    db_quote = session.scalar(select(Quote).where(and_(Quote.id == quote_id, Quote.tenant == context.tenant)))
                    if db_quote and db_quote.partyB != hedger_context.hedger_address:
                        continue
                    if db_quote:
                        print(
                            f"{context.tenant} => Contract: {key} Local DB: {db_quote.id}-{db_quote.openPrice}-{db_quote.closedAmount}-{db_quote.quantity}"
                        )
                    else:
                        print(f"{context.tenant} => Contract opened quote not found in the subgraph: {key}")

    # ------------------------------------------

    snapshot.accounts_count = (
        session.scalar(
            select(func.count(Account.id)).where(
                and_(
                    Account.blockNumber < block.number,
                    Account.timestamp > from_time,
                    Account.accountSource == affiliate_context.symmio_multi_account,
                    Account.tenant == context.tenant,
                )
            )
        )
        or 0
    )
    active_timestamp = block.datetime() - timedelta(hours=48)
    snapshot.active_accounts = (
        session.scalar(
            select(func.count(Account.id)).where(
                and_(
                    Account.blockNumber < block.number,
                    Account.accountSource == affiliate_context.symmio_multi_account,
                    Account.lastActivityTimestamp > active_timestamp,
                    Account.timestamp > from_time,
                    Account.tenant == context.tenant,
                )
            )
        )
        or 0
    )
    snapshot.users_count = (
        session.scalar(
            select(func.count(func.distinct(Account.user_id))).where(
                and_(
                    Account.blockNumber < block.number,
                    Account.accountSource == affiliate_context.symmio_multi_account,
                    Account.timestamp > from_time,
                    Account.tenant == context.tenant,
                )
            )
        )
        or 0
    )
    snapshot.active_users = (
        session.scalar(
            select(func.count(func.distinct(Account.user_id))).where(
                and_(
                    Account.blockNumber < block.number,
                    Account.accountSource == affiliate_context.symmio_multi_account,
                    Account.lastActivityTimestamp > active_timestamp,
                    Account.timestamp > from_time,
                    Account.tenant == context.tenant,
                )
            )
        )
        or 0
    )

    # ------------------------------------------
    for liquidator in affiliate_context.symmio_liquidators:
        account_withdraw = session.scalar(
            select(func.sum(BalanceChange.amount)).where(
                and_(
                    BalanceChange.collateral == context.symmio_collateral_address,
                    BalanceChange.type == BalanceChangeType.WITHDRAW,
                    BalanceChange.account_id == liquidator,
                    BalanceChange.blockNumber <= block.number,
                    BalanceChange.tenant == context.tenant,
                )
            )
        ) or Decimal(0)
        liquidator_state = {
            "address": liquidator,
            "withdraw": int(account_withdraw) * 10 ** (18 - config.decimals),
            "balance": contract_multicallable.balanceOf([snapshot_context.w3.to_checksum_address(liquidator)]).call(block_identifier=block.number)[0],
            "allocated": contract_multicallable.balanceInfoOfPartyA([snapshot_context.w3.to_checksum_address(liquidator)]).call(
                block_identifier=block.number
            )[0][0],
        }
        if "liquidator_states" not in snapshot:
            snapshot.liquidator_states = []
        snapshot.liquidator_states.append(liquidator_state)

    # ------------------------------------------
    snapshot.platform_fee = (
        session.scalar(
            select(func.sum(DailyHistory.platformFee)).where(
                and_(
                    DailyHistory.timestamp <= block.datetime(),
                    DailyHistory.timestamp > from_time,
                    DailyHistory.accountSource == affiliate_context.symmio_multi_account,
                    DailyHistory.tenant == context.tenant,
                )
            )
        )
        or 0
    )

    snapshot.trade_volume = (
        session.scalar(
            select(func.sum(DailyHistory.tradeVolume)).where(
                and_(
                    DailyHistory.timestamp <= block.datetime(),
                    DailyHistory.timestamp > from_time,
                    DailyHistory.accountSource == affiliate_context.symmio_multi_account,
                    DailyHistory.tenant == context.tenant,
                )
            )
        )
        or 0
    )

    snapshot.timestamp = block.datetime()
    snapshot.name = affiliate_context.name
    snapshot.hedger_name = hedger_context.name
    snapshot.account_source = affiliate_context.symmio_multi_account
    snapshot.tenant = context.tenant
    snapshot.block_number = block.number
    affiliate_snapshot = AffiliateSnapshot(**snapshot)
    affiliate_snapshot.save(session)
    return affiliate_snapshot


def calculate_notional_value(
    context,
    session: Session,
    affiliate_context: AffiliateContext,
    hedger_context: HedgerContext,
    quote_status,
    from_time,
    block: Block,
):
    return (
        session.scalar(
            select(func.sum(TradeHistory.volume))
            .join(Account)  # Implicitly joins TradeHistory to Account
            .join(TradeHistory.quote)  # Assumes there's a relationship set on TradeHistory named 'quote' to join with Quote
            .where(
                and_(
                    TradeHistory.blockNumber <= block.number,
                    Account.accountSource == affiliate_context.symmio_multi_account,
                    TradeHistory.quoteStatus == quote_status,
                    Quote.partyB == hedger_context.hedger_address,
                    TradeHistory.timestamp > from_time,
                    TradeHistory.tenant == context.tenant,
                )
            )
        )
        or 0
    )


def calculate_hedger_upnl(
    context,
    session: Session,
    affiliate_context,
    hedger_context,
    from_time,
    block: Block,
):
    if hedger_context.utils.binance_client:
        prices = hedger_context.utils.binance_client.futures_mark_price()
    else:
        prices = context.hedgers[0].utils.binance_client.futures_mark_price()  # FIXME: Find a better way later

    prices_map = {}
    for p in prices:
        prices_map[p["symbol"]] = p["markPrice"]

    party_b_opened_quotes = session.scalars(
        select(
            Quote,
        )
        .options(
            joinedload(Quote.symbol).load_only(Symbol.name),
            load_only(
                Quote.id,
                Quote.quantity,
                Quote.closedAmount,
                Quote.openPrice,
                Quote.positionType,
            ),
        )
        .join(Symbol)
        .join(Account)
        .where(
            and_(
                Quote.blockNumber <= block.number,
                Account.accountSource == affiliate_context.symmio_multi_account,
                Quote.timestamp > from_time,
                Quote.partyB == hedger_context.hedger_address,
                or_(
                    Quote.quoteStatus == 4,
                    Quote.quoteStatus == 5,
                    Quote.quoteStatus == 6,
                ),
                Quote.tenant == context.tenant,
            )
        )
    )

    subgraph_open_quotes = []
    hedger_upnl = Decimal(0)
    for quote in party_b_opened_quotes:
        key = f"{quote.id}-{quote.openPrice}-{quote.closedAmount}-{quote.quantity}"
        subgraph_open_quotes.append(key)
        side_sign = 1 if quote.positionType == "0" else -1
        current_price = Decimal(prices_map[quote.symbol.name]) * 10**18
        hedger_upnl += side_sign * (quote.openPrice - current_price) * (quote.quantity - quote.closedAmount) // 10**18
    return hedger_upnl, subgraph_open_quotes


def calculate_pnl_of_hedger(
    context,
    session: Session,
    affiliate_context,
    hedger_context,
    quote_status,
    from_time,
    block: Block,
):
    party_b_quotes = session.scalars(
        select(Quote)
        .options(
            load_only(
                Quote.quantity,
                Quote.avgClosedPrice,
                Quote.openPrice,
                Quote.positionType,
            )
        )
        .join(Account)
        .where(
            and_(
                Account.accountSource == affiliate_context.symmio_multi_account,
                Quote.partyB == hedger_context.hedger_address,
                Quote.quoteStatus == quote_status,
                Quote.timestamp > from_time,
                Quote.blockNumber <= block.number,
                Quote.tenant == context.tenant,
            )
        )
    )
    pnl = Decimal(0)
    for quote in party_b_quotes:
        if quote.positionType == "0":
            pnl -= Decimal(int(quote.quantity) * (int(quote.avgClosedPrice) - int(quote.openPrice)) / 10**18)
        else:
            pnl -= Decimal(int(quote.quantity) * (int(quote.openPrice) - int(quote.avgClosedPrice)) / 10**18)
    return pnl


def count_quotes_per_status(
    session: Session,
    affiliate_context,
    hedger_context: HedgerContext,
    context,
    from_time,
    block: Block,
):
    q_counts = session.execute(
        select(Quote.quoteStatus, func.count(Quote.id).label("count"))
        .join(Account)
        .where(
            and_(
                Quote.timestamp > from_time,
                Quote.blockNumber <= block.number,
                Account.accountSource == affiliate_context.symmio_multi_account,
                Quote.tenant == context.tenant,
                Quote.partyB == hedger_context.hedger_address,
            )
        )
        .group_by(Quote.quoteStatus)
    ).all()
    status_quotes = {}
    for item in q_counts:
        status_quotes[item[0]] = item[1]
    return status_quotes
