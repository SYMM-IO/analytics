import hmac
import time
from datetime import datetime, timedelta
from decimal import Decimal

import requests
from peewee import fn

from app.models import BinanceDeposit, BinanceWithdraw, BinanceTransfer, FundingRate, SymbolPrice
from config.local_settings import binance_email, binance_is_master, from_unix_timestamp
from config.settings import proxies
from context.context import binance_client
from utils.common_utils import load_config


def _get_signature(query_string, api_secret):
    return hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), digestmod='sha256').hexdigest()


def fetch_funding_rate_history(symbol: str):
    latest_record = FundingRate.select().where(FundingRate.symbol == symbol).order_by(
        FundingRate.timestamp.desc()).first()
    if latest_record:
        last_timestamp = round(latest_record.timestamp.timestamp() * 1000)
    else:
        last_timestamp = from_unix_timestamp - 1000
    page = 1
    history = []
    limit = 10000
    while True:
        # data = binance_client.history(symbol=symbol, page=page, rows=limit)
        json_data = {
            'symbol': symbol,
            'page': page,
            'rows': limit,
        }
        url = 'https://www.binance.com/bapi/futures/v1/public/future/common/get-funding-rate-history'
        response = requests.post(url, json=json_data, proxies=proxies)
        if not response:
            continue
        data = response.json()['data']
        assert type(data) == list
        if not data:
            break
        page += 1
        if data[-1]['calcTime'] <= last_timestamp:
            history.extend(filter(lambda x: x['calcTime'] > last_timestamp, data))
            break
        history.extend(data)
        if len(data) < limit:
            break

    for item in sorted(history, key=lambda x: x['calcTime']):
        FundingRate.create(
            symbol=item['symbol'],
            rate=Decimal(item['lastFundingRate']),
            timestamp=datetime.fromtimestamp(item['calcTime'] / 1000)
        )
    return history


def fetch_symbol_price_history(symbol: str):
    latest_record = SymbolPrice.select().where(SymbolPrice.symbol == symbol).order_by(
        SymbolPrice.timestamp.desc()).first()
    if latest_record:
        start_time = round(latest_record.timestamp.timestamp() * 1000) + 1000
    else:
        start_time = from_unix_timestamp
    # url = 'https://fapi.binance.com/fapi/v1/klines'
    timestamp = round(time.time() * 1000)
    while start_time < timestamp:
        data = binance_client.futures_klines(
            symbol=symbol,
            interval='1h',
            limit=1500,
            startTime=start_time
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
                symbol=symbol,
                price=close_price,
                timestamp=datetime.fromtimestamp(close_time / 1000),
            )
        start_time = close_time + 60_000


def fetch_binance_histories(model, fetch_function, timestamp_field, limit_days=88, asset_field="coin"):
    # Get the latest timestamp from the database for the respective model
    latest_record = model.select().order_by(model.timestamp.desc()).first()

    # If there's a record in the database, use its timestamp as the starting point
    if latest_record:
        start_time = latest_record.timestamp + timedelta(minutes=1)
    else:
        start_time = load_config().deployTimestamp

    end_time = start_time + timedelta(days=limit_days)
    current_time = datetime.utcnow()

    while start_time < current_time:
        print(f"{start_time=}, {end_time=}")
        data = fetch_function(startTime=int(start_time.timestamp() * 1000), endTime=int(end_time.timestamp() * 1000))

        if not data:
            start_time = end_time
            end_time = start_time + timedelta(days=limit_days)
            continue

        for item in data:
            model.create(
                asset=item[asset_field],
                amount=item['amount'],
                status=item['status'],
                timestamp=datetime.fromtimestamp(item[timestamp_field] / 1000)  # Convert from milliseconds
            )

        start_time = end_time
        end_time = start_time + timedelta(days=limit_days)


def fetch_binance_transfer_histories(model, fetch_function, timestamp_field, limit_days=29, asset_field="coin"):
    # Get the latest timestamp from the database for the respective model
    latest_record = model.select().order_by(model.timestamp.desc()).first()

    # If there's a record in the database, use its timestamp as the starting point
    if latest_record:
        start_time = latest_record.timestamp + timedelta(minutes=1)
    else:
        start_time = load_config().deployTimestamp

    end_time = start_time + timedelta(days=limit_days)
    current_time = datetime.utcnow()

    while start_time < current_time:
        print(f"{start_time=}, {end_time=}")
        data = fetch_function(startTime=int(start_time.timestamp() * 1000), endTime=int(end_time.timestamp() * 1000))
        if not data:
            start_time = end_time
            end_time = start_time + timedelta(days=limit_days)
            continue

        for item in data:
            model.create(
                asset=item[asset_field],
                frm=item['fromEmail'],
                to=item['toEmail'],
                amount=item['amount'],
                status=item['status'],
                timestamp=datetime.fromtimestamp(item[timestamp_field] / 1000)  # Convert from milliseconds
            )

        start_time = end_time
        end_time = start_time + timedelta(days=limit_days)


def update_binance_deposit():
    print("Updating Binance Deposits")
    print("Deposit .")
    fetch_binance_histories(BinanceDeposit, binance_client.get_deposit_history, 'insertTime')
    print("Withdraw .")
    fetch_binance_histories(BinanceWithdraw, binance_client.get_withdraw_history, 'applyTime')
    print("Transfers .")
    fetch_binance_transfer_histories(BinanceTransfer,
                                     binance_client.get_universal_transfer_history if binance_is_master
                                     else binance_client.get_subaccount_transfer_history,
                                     'createTimeStamp', asset_field="asset", limit_days=29)
    total_deposit = BinanceDeposit.select(fn.SUM(BinanceDeposit.amount)).scalar() or 0.0
    total_withdraw = BinanceWithdraw.select(fn.SUM(BinanceWithdraw.amount)).scalar() or 0.0
    total_transfers = (BinanceTransfer.select(fn.SUM(BinanceTransfer.amount))
                       .where(BinanceTransfer.frm == binance_email).scalar() or 0.0)
    balance = total_deposit - total_withdraw - total_transfers
    config = load_config()
    config.binanceDeposit = balance * 10 ** 18
    config.save()
