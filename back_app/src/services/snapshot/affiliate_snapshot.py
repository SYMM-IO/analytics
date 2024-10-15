import json
from datetime import datetime, timedelta
from decimal import Decimal

from binance.um_futures import UMFutures
from sqlalchemy import func, and_, or_, select
from sqlalchemy.orm import Session, load_only, joinedload

from src.app import log_span_context
from src.app.models import (
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
from src.config.settings import (
    AffiliateContext,
    HedgerContext,
    Context,
    DEBUG_MODE,
)
from src.services.snapshot.snapshot_context import SnapshotContext
from src.utils.attr_dict import AttrDict
from src.utils.block import Block
from src.utils.model_utils import log_object_properties


def prepare_affiliate_snapshot(
    snapshot_context: SnapshotContext, affiliate_context: AffiliateContext, hedger_context: HedgerContext, block: Block, transaction_id
):
    print(f"----------------Prepare Affiliate Snapshot Of {hedger_context.name} -> {affiliate_context.name}")
    context: Context = snapshot_context.context
    session: Session = snapshot_context.session
    config: RuntimeConfiguration = snapshot_context.config

    from_time = datetime.fromtimestamp(context.deploy_timestamp / 1000)
    snapshot = AttrDict()

    snapshot.status_quotes = json.dumps(count_quotes_per_status(session, affiliate_context, hedger_context, context, from_time, block))
    snapshot.pnl_of_closed = calculate_pnl_of_hedger(context, session, affiliate_context, hedger_context, 7, from_time, block)
    snapshot.pnl_of_liquidated = calculate_pnl_of_hedger(context, session, affiliate_context, hedger_context, 8, from_time, block)
    snapshot.hedger_upnl, local_open_quotes = calculate_hedger_upnl(context, session, affiliate_context, hedger_context, from_time, block)
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
                    Quote.liquidatedSide == 0,
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
                    Quote.liquidatedSide == 1,
                    Quote.timestamp > from_time,
                    Quote.blockNumber <= block.number,
                    Quote.tenant == context.tenant,
                )
            )
        )
        or 0
    )

    # ------------------------------------------
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
    hedger_addr = snapshot_context.context.w3.to_checksum_address(hedger_context.hedger_address)
    snapshot.hedger_contract_allocated = Decimal(
        sum(
            snapshot_context.multicallable.allocatedBalanceOfPartyB(
                [(hedger_addr, snapshot_context.context.w3.to_checksum_address(a.id)) for a in all_accounts]
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
        print(f"{context.tenant}: Checking diff of open quotes with subgraph")

        party_a_open_positions = snapshot_context.multicallable.getPartyAOpenPositions(
            [(snapshot_context.context.w3.to_checksum_address(a.id), 0, 100) for a in all_accounts]
        ).call(n=pages_count, block_identifier=block.number)

        for party_a_quotes in party_a_open_positions:
            for quote in party_a_quotes:
                # key = f"{quote.id}-{quote.openPrice}-{quote.closedAmount}-{quote.quantity}"
                key = f"{context.tenant}_{quote[0]}-{quote[5]}-{quote[10]}-{quote[9]}-{quote[16]}"
                quote_id = f"{context.tenant}_{quote[0]}"
                if key not in local_open_quotes:
                    db_quote = session.scalar(select(Quote).where(and_(Quote.id == quote_id, Quote.tenant == context.tenant)))
                    if db_quote and db_quote.partyB != hedger_context.hedger_address:
                        continue
                    db_account = session.scalar(select(Account).where(and_(Account.id == db_quote.account_id, Account.tenant == context.tenant)))
                    if db_account.accountSource != affiliate_context.symmio_multi_account:
                        continue
                    if db_quote:
                        local_key = f"{db_quote.id}-{db_quote.openedPrice}-{db_quote.closedAmount}-{db_quote.quantity}-{db_quote.quoteStatus}"
                        print(f"{context.tenant} => We have diff: Contract: {key} Local DB: {local_key}")
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
    with log_span_context(session, "Prepare Affiliate Snapshot", transaction_id) as log_span:
        affiliate_snapshot_details = log_object_properties(affiliate_snapshot)
        log_span.add_data("affiliate_snapshot", affiliate_snapshot_details)
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
        session.scalar(  # Implicitly joins TradeHistory to Account
            select(func.sum(TradeHistory.volume))
            .join(Account)
            .join(TradeHistory.quote)
            .where(
                # Assumes there's a relationship set on TradeHistory named 'quote' to join with Quote
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
    hedger_context: HedgerContext,
    from_time,
    block: Block,
):
    prices = UMFutures().ticker_price()
    prices_map = {}
    for p in prices:
        prices_map[p["symbol"]] = p["price"]

    party_b_opened_quotes = session.scalars(
        select(Quote)
        .options(
            joinedload(Quote.symbol).load_only(Symbol.name),
            load_only(
                Quote.id,
                Quote.quantity,
                Quote.closedAmount,
                Quote.openedPrice,
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

    local_open_quotes = []
    hedger_upnl = Decimal(0)
    for quote in party_b_opened_quotes:
        key = f"{quote.id}-{quote.openedPrice}-{quote.closedAmount}-{quote.quantity}-{quote.quoteStatus}"
        local_open_quotes.append(key)
        side_sign = 1 if quote.positionType == "0" else -1
        current_price = Decimal(prices_map[quote.symbol.name]) * 10**18
        hedger_upnl += side_sign * (quote.openedPrice - current_price) * (quote.quantity - quote.closedAmount) // 10**18
    return hedger_upnl, local_open_quotes


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
                Quote.averageClosedPrice,
                Quote.openedPrice,
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
            pnl -= Decimal(int(quote.quantity) * (int(quote.averageClosedPrice) - int(quote.openedPrice)) / 10**18)
        else:
            pnl -= Decimal(int(quote.quantity) * (int(quote.openedPrice) - int(quote.averageClosedPrice)) / 10**18)
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
