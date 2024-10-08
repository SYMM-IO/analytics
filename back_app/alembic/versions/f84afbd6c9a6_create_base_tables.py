"""Create base tables

Revision ID: f84afbd6c9a6
Revises:
Create Date: 2024-03-06 14:04:42.453254

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f84afbd6c9a6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "admin_user",
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=True),
        sa.Column("createTimestamp", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("username"),
    )
    op.create_table(
        "affiliate_snapshot",
        sa.Column("status_quotes", sa.Text(), nullable=True),
        sa.Column("pnl_of_closed", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("pnl_of_liquidated", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("closed_notional_value", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column(
            "liquidated_notional_value",
            sa.Numeric(precision=40, scale=0),
            nullable=True,
        ),
        sa.Column("opened_notional_value", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("earned_cva", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("loss_cva", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column(
            "hedger_contract_allocated",
            sa.Numeric(precision=40, scale=0),
            nullable=True,
        ),
        sa.Column("hedger_upnl", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("all_contract_deposit", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("all_contract_withdraw", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("platform_fee", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("accounts_count", sa.Integer(), nullable=True),
        sa.Column("active_accounts", sa.Integer(), nullable=True),
        sa.Column("users_count", sa.Integer(), nullable=True),
        sa.Column("active_users", sa.Integer(), nullable=True),
        sa.Column("trade_volume", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("block_number", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("account_source", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("hedger_name", sa.String(), nullable=False),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("timestamp", "tenant", "name", "hedger_name"),
    )
    op.create_table(
        "liquidator_snapshot",
        sa.Column("withdraw", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("balance", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("allocated", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("timestamp", "tenant", "address"),
    )
    op.create_table(
        "binance_income",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.Column("hedger", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "binance_trade",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=True),
        sa.Column("order_id", sa.String(), nullable=True),
        sa.Column("side", sa.String(), nullable=True),
        sa.Column("position_side", sa.String(), nullable=True),
        sa.Column("qty", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("price", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.Column("hedger", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "daily_history",
        sa.Column("id", sa.String(), nullable=True),
        sa.Column("quotesCount", sa.Integer(), nullable=True),
        sa.Column("newUsers", sa.Integer(), nullable=True),
        sa.Column("accountSource", sa.String(), nullable=True),
        sa.Column("newAccounts", sa.Integer(), nullable=True),
        sa.Column("activeUsers", sa.Integer(), nullable=True),
        sa.Column("tradeVolume", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("deposit", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("withdraw", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("allocate", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("deallocate", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("platformFee", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("openInterest", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("updateTimestamp", sa.DateTime(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("timestamp"),
    )
    op.create_table(
        "hedger_snapshot",
        sa.Column("hedger_contract_balance", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("hedger_contract_deposit", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("hedger_contract_withdraw", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("users_paid_funding_fee", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("users_received_funding_fee", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("contract_profit", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("liquidators_profit", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("total_deposit", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("earned_cva", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("loss_cva", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("liquidators_balance", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("liquidators_withdraw", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("liquidators_allocated", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("gas", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("block_number", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("name", sa.String(), nullable=False, primary_key=True),
        sa.Column("tenant", sa.String(), nullable=False, primary_key=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, primary_key=True),
    )
    op.create_table(
        "hedger_binance_snapshot",
        sa.Column("max_open_interest", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("binance_maintenance_margin", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("binance_total_balance", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("binance_account_health_ratio", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("binance_cross_upnl", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("binance_av_balance", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("binance_total_initial_margin", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("binance_max_withdraw_amount", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("binance_deposit", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("binance_trade_volume", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("binance_paid_funding_fee", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("binance_received_funding_fee", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("users_paid_funding_fee", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("users_received_funding_fee", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("binance_next_funding_fee", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("binance_profit", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("total_deposit", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("block_number", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("name", sa.String(), nullable=False, primary_key=True),
        sa.Column("tenant", sa.String(), nullable=False, primary_key=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, primary_key=True),
    )
    op.create_table(
        "runtime_configuration",
        sa.Column("tenant", sa.String(), nullable=False, primary_key=True),
        sa.Column("decimals", sa.Integer(), nullable=True),
        sa.Column("lastHistoricalSnapshotBlock", sa.Integer(), nullable=True),
        sa.Column("lastSnapshotBlock", sa.Integer(), nullable=True),
        sa.Column("lastSyncBlock", sa.Integer()),
        sa.Column("snapshotBlockLag", sa.Integer()),
        sa.Column("deployTimestamp", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("tenant"),
    )
    op.create_table(
        "stats_bot_message",
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("content", sa.JSON(), nullable=True),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("message_id", "tenant"),
    )
    op.create_table(
        "symbol",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("tradingFee", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("updateTimestamp", sa.DateTime(), nullable=True),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("transaction", sa.String(), nullable=True),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "account",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("accountSource", sa.String(), nullable=True),
        sa.Column("quotesCount", sa.Integer(), nullable=True),
        sa.Column("positionsCount", sa.Integer(), nullable=True),
        sa.Column("transaction", sa.String(), nullable=True),
        sa.Column("lastActivityTimestamp", sa.DateTime(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("blockNumber", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("updateTimestamp", sa.DateTime(), nullable=True),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "balance_change",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("account_id", sa.String(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("collateral", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("blockNumber", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("transaction", sa.String(), nullable=True),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "quote",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("account_id", sa.String(), nullable=True),
        sa.Column("averageClosedPrice", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("blockNumber", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("closeDeadline", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("closePrice", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("closedAmount", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("closedPrice", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("cva", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("fillAmount", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("initialCva", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("initialLf", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("initialOpenedPrice", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("initialPartyAmm", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("initialPartyBmm", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("lf", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("liquidateAmount", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("liquidatedSide", sa.Integer(), nullable=True),
        sa.Column("liquidatePrice", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("marketPrice", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("maxFundingRate", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("openDeadline", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("openedPrice", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("orderTypeClose", sa.String(), nullable=True),
        sa.Column("orderTypeOpen", sa.String(), nullable=True),
        sa.Column("partyAmm", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("partyB", sa.String(), nullable=True),
        sa.Column("partyBmm", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("partyBsWhiteList", sa.Text(), nullable=True),
        sa.Column("positionType", sa.String(), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("quantityToClose", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("quoteStatus", sa.Integer(), nullable=True),
        sa.Column("requestedOpenPrice", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("symbol_id", sa.String(), nullable=True),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("timestampAcceptCancelCloseRequest", sa.DateTime(), nullable=True),
        sa.Column("timestampAcceptCancelRequest", sa.DateTime(), nullable=True),
        sa.Column("timestampChargeFundingRate", sa.DateTime(), nullable=True),
        sa.Column("timestampEmergencyClosePosition", sa.DateTime(), nullable=True),
        sa.Column("timestampExpireQuote", sa.DateTime(), nullable=True),
        sa.Column("timestampFillCloseRequest", sa.DateTime(), nullable=True),
        sa.Column("timestampForceCancelCloseRequest", sa.DateTime(), nullable=True),
        sa.Column("timestampForceCancelQuote", sa.DateTime(), nullable=True),
        sa.Column("timestampForceClosePosition", sa.DateTime(), nullable=True),
        sa.Column("timestampLastFundingPayment", sa.DateTime(), nullable=True),
        sa.Column("timestampLiquidatePositionsPartyA", sa.DateTime(), nullable=True),
        sa.Column("timestampLiquidatePositionsPartyB", sa.DateTime(), nullable=True),
        sa.Column("timestampLockQuote", sa.DateTime(), nullable=True),
        sa.Column("timestampOpenPosition", sa.DateTime(), nullable=True),
        sa.Column("timestampRequestToCancelCloseRequest", sa.DateTime(), nullable=True),
        sa.Column("timestampRequestToCancelQuote", sa.DateTime(), nullable=True),
        sa.Column("timestampRequestToClosePosition", sa.DateTime(), nullable=True),
        sa.Column("timestampRequestToLimitClosePosition", sa.DateTime(), nullable=True),
        sa.Column("timestampSendQuote", sa.DateTime(), nullable=True),
        sa.Column("timestampUnlockQuote", sa.DateTime(), nullable=True),
        sa.Column("tradingFee", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("userPaidFunding", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("userReceivedFunding", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
        ),
        sa.ForeignKeyConstraint(
            ["symbol_id"],
            ["symbol.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "trade_history",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("account_id", sa.String(), nullable=True),
        sa.Column("quote_id", sa.String(), nullable=True),
        sa.Column("volume", sa.Numeric(precision=40, scale=0), nullable=True),
        sa.Column("blockNumber", sa.Integer(), nullable=True),
        sa.Column("transaction", sa.String(), nullable=True),
        sa.Column("quoteStatus", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("updateTimestamp", sa.DateTime(), nullable=True),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
        ),
        sa.ForeignKeyConstraint(
            ["quote_id"],
            ["quote.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "gas_history",
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("gas_amount", sa.Numeric(precision=40, scale=0), nullable=False),
        sa.Column("initial_block", sa.Integer(), nullable=False),
        sa.Column("tx_count", sa.Integer(), nullable=False),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("address", "tenant"),
    )
    op.create_table(
        "log_transaction",
        sa.Column("id", sa.Integer()),
        sa.Column("label", sa.String()),
        sa.Column("tenant", sa.String()),
        sa.Column("data", sa.JSON()),
        sa.Column("start_time", sa.DateTime()),
        sa.Column("end_time", sa.DateTime()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "log_span",
        sa.Column("id", sa.Integer()),
        sa.Column("transaction_id", sa.Integer()),
        sa.Column("label", sa.String()),
        sa.Column("data", sa.JSON()),
        sa.Column("start_time", sa.DateTime()),
        sa.Column("end_time", sa.DateTime()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["log_transaction.id"],
        ),
    )


# ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("trade_history")
    op.drop_table("quote")
    op.drop_table("balance_change")
    op.drop_table("account")
    op.drop_table("user")
    op.drop_table("symbol")
    op.drop_table("stats_bot_message")
    op.drop_table("runtime_configuration")
    op.drop_table("hedger_snapshot")
    op.drop_table("hedger_binance_snapshot")
    op.drop_table("liquidator_snapshot")
    op.drop_table("daily_history")
    op.drop_table("binance_trade")
    op.drop_table("binance_income")
    op.drop_table("affiliate_snapshot")
    op.drop_table("admin_user")
    op.drop_table("gas_history")
    op.drop_table("log_span")
    op.drop_table("log_transaction")
    # ### end Alembic commands ###
