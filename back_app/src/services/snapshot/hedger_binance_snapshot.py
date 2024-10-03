from decimal import Decimal

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from src.app import log_span_context
from src.app.models import (
    BinanceIncome,
    HedgerBinanceSnapshot,
)
from src.config.settings import (
    Context,
    HedgerContext,
    IGNORE_BINANCE_TRADE_VOLUME,
)
from src.services.binance_service import real_time_funding_rate
from src.services.binance_trade_volume_service import calculate_binance_trade_volume
from src.services.snapshot.snapshot_context import SnapshotContext
from src.utils.attr_dict import AttrDict
from src.utils.block import Block
from src.utils.model_utils import log_object_properties


def prepare_hedger_binance_snapshot(snapshot_context: SnapshotContext, hedger_context: HedgerContext, block: Block, transaction_id):
    print(f"----------------Prepare Hedger Binance Snapshot Of {hedger_context.name}")
    context: Context = snapshot_context.context
    session: Session = snapshot_context.session

    snapshot = AttrDict()

    transfer_sum = session.execute(
        select(func.coalesce(func.sum(BinanceIncome.amount), 0)).where(
            and_(
                BinanceIncome.timestamp <= block.datetime(),
                BinanceIncome.type == "TRANSFER",
                BinanceIncome.tenant == context.tenant,
                BinanceIncome.hedger == hedger_context.name,
            )
        )
    ).scalar_one()

    internal_transfer_sum = session.execute(
        select(func.coalesce(func.sum(BinanceIncome.amount), 0)).where(
            and_(
                BinanceIncome.timestamp <= block.datetime(),
                BinanceIncome.type == "INTERNAL_TRANSFER",
                BinanceIncome.tenant == context.tenant,
                BinanceIncome.hedger == hedger_context.name,
            )
        )
    ).scalar_one()

    total_transfers = transfer_sum + internal_transfer_sum

    is_negative = total_transfers < 0
    snapshot.binance_deposit = (
        Decimal(-(abs(total_transfers) * 10**18) if is_negative else total_transfers * 10**18) + hedger_context.binance_deposit_diff
    )

    if not block.is_for_past():
        binance_account = hedger_context.utils.binance_client.futures_account(version=2)
        snapshot.binance_maintenance_margin = Decimal(float(binance_account["totalMaintMargin"]) * 10**18)
        snapshot.binance_total_balance = Decimal(float(binance_account["totalMarginBalance"]) * 10**18)
        snapshot.binance_account_health_ratio = 100 - (snapshot.binance_maintenance_margin / snapshot.binance_total_balance) * 100
        snapshot.binance_cross_upnl = Decimal(binance_account["totalCrossUnPnl"]) * 10**18
        snapshot.binance_av_balance = Decimal(binance_account["availableBalance"]) * 10**18
        snapshot.binance_total_initial_margin = Decimal(binance_account["totalInitialMargin"]) * 10**18
        snapshot.binance_max_withdraw_amount = Decimal(binance_account["maxWithdrawAmount"]) * 10**18
        snapshot.max_open_interest = Decimal(hedger_context.hedger_max_open_interest_ratio * snapshot.binance_max_withdraw_amount)
    else:
        ...
        # stat_message = session.scalar(
        #     select(StatsBotMessage).where(
        #         and_(
        #             StatsBotMessage.timestamp <= block.datetime(),
        #             StatsBotMessage.timestamp >= block.datetime() - datetime.timedelta(minutes=3),
        #             StatsBotMessage.tenant == context.tenant,
        #         )
        #     )
        # )
        # FIXME  begin{
        # if not stat_message:
        #     raise Exception(f"{context.tenant}: StatBot message not found for date: {block.datetime()}")

        snapshot.binance_maintenance_margin = 0  # stat_message.content["Total Maint. Margin"]
        snapshot.binance_total_balance = 0  # stat_message.content["Total Margin Balance"]
        snapshot.binance_account_health_ratio = 0  # stat_message.content["Health Ratio"]
        snapshot.binance_cross_upnl = 0  # stat_message.content["Total Cross UnPnl"]
        snapshot.binance_av_balance = 0  # stat_message.content["Available Balance"]
        snapshot.binance_total_initial_margin = 0  # stat_message.content["Total Initial Margin"]
        snapshot.binance_max_withdraw_amount = 0  # stat_message.content["Max Withdraw Amount"]
        snapshot.max_open_interest = 0  # Decimal(hedger_context.hedger_max_open_interest_ratio * snapshot.binance_max_withdraw_amount)
        # FIXME  }end

    snapshot.binance_profit = snapshot.binance_total_balance - (snapshot.binance_deposit or Decimal(0))
    snapshot.binance_trade_volume = (
        0 if IGNORE_BINANCE_TRADE_VOLUME else Decimal(calculate_binance_trade_volume(context, session, hedger_context, block) * 10**18)
    )

    # ------------------------------------------
    snapshot.binance_paid_funding_fee = session.execute(
        select(func.coalesce(func.sum(BinanceIncome.amount), Decimal(0))).where(
            and_(
                BinanceIncome.timestamp <= block.datetime(),
                BinanceIncome.amount < 0,
                BinanceIncome.type == "FUNDING_FEE",
                BinanceIncome.tenant == context.tenant,
            )
        )
    ).scalar_one()

    snapshot.binance_received_funding_fee = session.execute(
        select(func.coalesce(func.sum(BinanceIncome.amount), Decimal(0))).where(
            and_(
                BinanceIncome.timestamp <= block.datetime(),
                BinanceIncome.amount > 0,
                BinanceIncome.type == "FUNDING_FEE",
                BinanceIncome.tenant == context.tenant,
            )
        )
    ).scalar_one()

    if not block.is_for_past():
        positions = hedger_context.utils.binance_client.futures_position_information()
        open_positions = [p for p in positions if Decimal(p["notional"]) != 0]
        binance_next_funding_fee = 0
        for pos in open_positions:
            notional, symbol, _ = (
                Decimal(pos["notional"]),
                pos["symbol"],
                pos["positionSide"],
            )
            funding_rate = pos["fundingRate"] = real_time_funding_rate(symbol=symbol)
            funding_rate_fee = -1 * notional * funding_rate
            binance_next_funding_fee += funding_rate_fee * 10**18

        snapshot.binance_next_funding_fee = binance_next_funding_fee

    snapshot.timestamp = block.datetime()
    snapshot.name = hedger_context.name
    snapshot.tenant = context.tenant
    snapshot.block_number = block.number
    print(snapshot)
    hedger_binance_snapshot = HedgerBinanceSnapshot(**snapshot)
    with log_span_context(session, "Prepare Hedger Binance Snapshot", transaction_id) as log_span:
        hedger_binance_snapshot_details = log_object_properties(hedger_binance_snapshot)
        log_span.add_data("hedger_binance_snapshot", hedger_binance_snapshot_details)
    hedger_binance_snapshot.save(session)
    return hedger_binance_snapshot
