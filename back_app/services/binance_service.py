import time
from datetime import datetime, timedelta

from peewee import fn

from app.models import (
    BinanceIncome,
)
from config.settings import Context, HedgerContext
from services.config_service import load_config


def fetch_binance_income_histories(
    context: Context,
    hedger_context: HedgerContext,
    model,
    fetch_function,
    timestamp_field,
    income_type,
    limit_days=7,
    asset_field="asset",
):
    # Get the latest timestamp from the database for the respective model
    latest_record = (
        model.select()
        .where(model.tenant == context.tenant, model.type == income_type)
        .order_by(model.timestamp.desc())
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
            f"{context.tenant}: Fetching binance income histories between {start_time} and {end_time}"
        )
        time.sleep(5)
        data = fetch_function(
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
            model.create(
                tenant=context.tenant,
                asset=item[asset_field],
                amount=item["income"],
                type=item["incomeType"],
                hedger=hedger_context.name,
                timestamp=datetime.fromtimestamp(
                    item[timestamp_field] / 1000
                ),  # Convert from milliseconds
            )
        if len(data) == 1000:
            start_time = datetime.fromtimestamp(data[-1][timestamp_field] / 1000)
        else:
            start_time = end_time
        end_time = start_time + timedelta(days=limit_days)


def update_binance_deposit(context: Context, hedger_context: HedgerContext):
    fetch_binance_income_histories(
        context,
        hedger_context,
        BinanceIncome,
        hedger_context.utils.binance_client.futures_income_history,
        "time",
        "FUNDING_FEE",
    )
    fetch_binance_income_histories(
        context,
        hedger_context,
        BinanceIncome,
        hedger_context.utils.binance_client.futures_income_history,
        "time",
        "TRANSFER",
    )
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
