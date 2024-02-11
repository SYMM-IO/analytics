import time
from datetime import datetime, timedelta

from peewee import fn

from app.models import (
    BinanceIncome,
)
from config.settings import Context, HedgerContext
from services.config_service import load_config


def fetch_binance_income_histories_of_type(
    context: Context,
    hedger_context: HedgerContext,
    income_type,
    limit_days=7,
    asset_field="asset",
):
    # Get the latest timestamp from the database for the respective model
    latest_record = (
        BinanceIncome.select()
        .where(
            BinanceIncome.tenant == context.tenant, BinanceIncome.type == income_type
        )
        .order_by(BinanceIncome.timestamp.desc())
        .first()
    )

    # If there's a record in the database, use its timestamp as the starting point
    if latest_record:
        start_time = latest_record.timestamp + timedelta(minutes=1)
    else:
        start_time = load_config(context).deployTimestamp

    end_time = start_time + timedelta(days=limit_days)
    current_time = datetime.utcnow()

    while start_time < current_time:
        print(
            f"{context.tenant}: Fetching binance {income_type} income histories between {start_time} and {end_time}"
        )
        time.sleep(5)
        data = hedger_context.utils.binance_client.futures_income_history(
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            limit=1000,
            incomeType=income_type,
        )
        if not data:
            start_time = end_time
            end_time = start_time + timedelta(days=limit_days)
            continue

        for item in data:
            BinanceIncome.create(
                tenant=context.tenant,
                asset=item[asset_field],
                amount=item["income"],
                type=item["incomeType"],
                hedger=hedger_context.name,
                timestamp=datetime.fromtimestamp(
                    item["time"] / 1000
                ),  # Convert from milliseconds
            )
        if len(data) == 1000:
            start_time = datetime.fromtimestamp(data[-1]["time"] / 1000)
        else:
            start_time = end_time
        end_time = start_time + timedelta(days=limit_days)


def fetch_binance_income_histories(context, hedger_context):
    fetch_binance_income_histories_of_type(
        context,
        hedger_context,
        "FUNDING_FEE",
    )
    fetch_binance_income_histories_of_type(
        context,
        hedger_context,
        "TRANSFER",
    )


def update_binance_deposit(context: Context, hedger_context: HedgerContext):
    total_transfers = (
        BinanceIncome.select(fn.SUM(BinanceIncome.amount))
        .where(
            BinanceIncome.type == "TRANSFER",
            BinanceIncome.tenant == context.tenant,
            BinanceIncome.hedger == hedger_context.name,
        )
        .scalar()
        or 0.0
    )
    is_negative = total_transfers < 0
    config = load_config(context)
    config.binanceDeposit = (
        -(abs(total_transfers) * 10**18)
        if is_negative
        else total_transfers * 10**18
    )
    config.save()
