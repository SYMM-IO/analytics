import hmac
import time
from datetime import datetime, timedelta
from decimal import Decimal

import requests
from peewee import fn

from app.models import (
    BinanceDeposit,
    BinanceWithdraw,
    BinanceTransfer,
    FundingRate,
    SymbolPrice,
    BinanceIncome,
)
from config.settings import proxies, Context
from utils.common_utils import load_config


def _get_signature(query_string, api_secret):
    return hmac.new(
        api_secret.encode("utf-8"), query_string.encode("utf-8"), digestmod="sha256"
    ).hexdigest()


def fetch_funding_rate_history(context: Context, symbol: str):
    latest_record = (
        FundingRate.select()
        .where(FundingRate.symbol == symbol)
        .order_by(FundingRate.timestamp.desc())
        .first()
    )
    if latest_record:
        last_timestamp = round(latest_record.timestamp.timestamp() * 1000)
    else:
        last_timestamp = context.from_unix_timestamp - 1000
    page = 1
    history = []
    limit = 10000
    while True:
        # data = binance_client.history(symbol=symbol, page=page, rows=limit)
        json_data = {
            "symbol": symbol,
            "page": page,
            "rows": limit,
        }
        url = "https://www.binance.com/bapi/futures/v1/public/future/common/get-funding-rate-history"
        response = requests.post(url, json=json_data, proxies=proxies)
        if not response:
            continue
        data = response.json()["data"]
        assert type(data) == list
        if not data:
            break
        page += 1
        if data[-1]["calcTime"] <= last_timestamp:
            history.extend(filter(lambda x: x["calcTime"] > last_timestamp, data))
            break
        history.extend(data)
        if len(data) < limit:
            break

    for item in sorted(history, key=lambda x: x["calcTime"]):
        FundingRate.create(
            tenant=context.tenant,
            symbol=item["symbol"],
            rate=Decimal(item["lastFundingRate"]),
            timestamp=datetime.fromtimestamp(item["calcTime"] / 1000),
        )
    return history


def fetch_symbol_price_history(context: Context, symbol: str):
    latest_record = (
        SymbolPrice.select()
        .where(SymbolPrice.symbol == symbol)
        .order_by(SymbolPrice.timestamp.desc())
        .first()
    )
    if latest_record:
        start_time = round(latest_record.timestamp.timestamp() * 1000) + 1000
    else:
        start_time = context.from_unix_timestamp
    # url = 'https://fapi.binance.com/fapi/v1/klines'
    timestamp = round(time.time() * 1000)
    while start_time < timestamp:
        data = context.utils.binance_client.futures_klines(
            symbol=symbol, interval="1h", limit=1500, startTime=start_time
        )
        # params = {
        #     'symbol': symbol,
        #     'interval': '1h',
        #     'limit': 1500,
        #     'startTime': start_time,
        # }
        # response = requests.get(url, params=params, proxies=proxies)
        if not data:
            break
        for item in data:
            close_price = Decimal(item[4])
            close_time = item[6]
            SymbolPrice.create(
                tenant=context.tenant,
                symbol=symbol,
                price=close_price,
                timestamp=datetime.fromtimestamp(close_time / 1000),
            )
        start_time = close_time + 60_000


def fetch_binance_histories(
    context: Context,
    model,
    fetch_function,
    timestamp_field,
    limit_days=88,
    asset_field="coin",
):
    # Get the latest timestamp from the database for the respective model
    latest_record = (
        model.select()
        .where(model.tenant == context.tenant)
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
        print(f"{context.tenant}: Fetching binance histories between {start_time} and {end_time}")
        data = fetch_function(
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
        )

        if not data:
            start_time = end_time
            end_time = start_time + timedelta(days=limit_days)
            continue

        for item in data:
            model.create(
                tenant=context.tenant,
                asset=item[asset_field],
                amount=item["amount"],
                status=item["status"],
                timestamp=datetime.fromtimestamp(
                    item[timestamp_field] / 1000
                ),  # Convert from milliseconds
            )

        start_time = end_time
        end_time = start_time + timedelta(days=limit_days)


def fetch_binance_transfer_histories(
    context: Context,
    model,
    fetch_function,
    timestamp_field,
    limit_days=29,
    asset_field="coin",
):
    # Get the latest timestamp from the database for the respective model
    latest_record = (
        model.select()
        .where(model.tenant == context.tenant)
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
        print(f"{context.tenant}: Fetching binance transfer histories between {start_time} and {end_time}")

        data = fetch_function(
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
        )
        if not data:
            start_time = end_time
            end_time = start_time + timedelta(days=limit_days)
            continue

        for item in data:
            model.create(
                tenant=context.tenant,
                asset=item[asset_field],
                frm=item["fromEmail"],
                to=item["toEmail"],
                amount=item["amount"],
                status=item["status"],
                timestamp=datetime.fromtimestamp(
                    item[timestamp_field] / 1000
                ),  # Convert from milliseconds
            )

        start_time = end_time
        end_time = start_time + timedelta(days=limit_days)


def fetch_binance_income_histories(
    context: Context,
    model,
    fetch_function,
    timestamp_field,
    limit_days=7,
    asset_field="asset",
):
    # Get the latest timestamp from the database for the respective model
    latest_record = (
        model.select()
        .where(model.tenant == context.tenant)
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
        print(f"{context.tenant}: Fetching binance income histories between {start_time} and {end_time}")
        data = fetch_function(
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            limit=1000,
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
                timestamp=datetime.fromtimestamp(
                    item[timestamp_field] / 1000
                ),  # Convert from milliseconds
            )

        if len(data) == 1000:
            start_time = datetime.fromtimestamp(data[-1][timestamp_field] / 1000)
        else:
            start_time = end_time
        end_time = start_time + timedelta(days=limit_days)


def update_binance_deposit(context: Context):
    print("Updating Binance Deposits")
    print("Deposit .")
    fetch_binance_histories(
        context,
        BinanceDeposit,
        context.utils.binance_client.get_deposit_history,
        "insertTime",
    )
    print("Withdraw .")
    fetch_binance_histories(
        context,
        BinanceWithdraw,
        context.utils.binance_client.get_withdraw_history,
        "applyTime",
    )
    print("Transfers .")
    fetch_binance_transfer_histories(
        context,
        BinanceTransfer,
        context.utils.binance_client.get_universal_transfer_history
        if context.binance_is_master
        else context.utils.binance_client.get_subaccount_transfer_history,
        "createTimeStamp",
        asset_field="asset",
        limit_days=29,
    )
    total_deposit = BinanceDeposit.select(fn.SUM(BinanceDeposit.amount)).scalar() or 0.0
    total_withdraw = (
        BinanceWithdraw.select(fn.SUM(BinanceWithdraw.amount)).scalar() or 0.0
    )
    total_transfers = (
        BinanceTransfer.select(fn.SUM(BinanceTransfer.amount))
        .where(
            BinanceTransfer.frm == context.binance_email,
            BinanceTransfer.tenant == context.tenant,
        )
        .scalar()
        or 0.0
    )
    balance = total_deposit - total_withdraw - total_transfers
    config = load_config(context)
    config.binanceDeposit = balance * 10**18
    config.save()


def update_binance_deposit_v2(context: Context):
    fetch_binance_income_histories(
        context,
        BinanceIncome,
        context.utils.binance_client.futures_income_history,
        "time",
    )
    total_transfers = (
        BinanceIncome.select(fn.SUM(BinanceIncome.amount))
        .where(BinanceIncome.type == "TRANSFER", BinanceIncome.tenant == context.tenant)
        .scalar()
        or 0.0
    )
    config = load_config(context)
    config.binanceDeposit = total_transfers * 10**18
    config.save()
