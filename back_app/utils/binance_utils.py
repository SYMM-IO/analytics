import hmac
import time
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import urlencode

import requests
from peewee import fn

from app.models import BinanceDeposit, BinanceWithdraw, BinanceTransfer, FundingRate, BinanceTrade, SymbolPrice
from config.local_settings import binance_email, binance_is_master, from_unix_timestamp, binance_api_key, \
    binance_api_secret
from config.settings import proxies
from context.context import binance_client
from utils.common_utils import load_config


def _get_signature(query_string, api_secret):
    return hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), digestmod='sha256').hexdigest()


def fetch_account_trades():
    latest_record = BinanceTrade.select().order_by(BinanceTrade.timestamp.desc()).first()
    if latest_record:
        start_time = round(latest_record.timestamp.timestamp() * 1000)
        last_id = latest_record.id
        last_symbol = latest_record.symbol
    else:
        start_time = from_unix_timestamp
        last_id = 0
        last_symbol = ''

    limit = 1000
    endpoint = 'https://fapi.binance.com/fapi/v1/userTrades'
    headers = {'X-MBX-APIKEY': binance_api_key}

    timestamp = round(time.time() * 1000)
    while start_time < timestamp:
        timestamp = round(time.time() * 1000)
        params = {
            'startTime': start_time,
            'timestamp': timestamp,
            'limit': limit,
        }
        query_string = urlencode(params)
        signature = _get_signature(query_string, binance_api_secret)
        url = f'{endpoint}?{query_string}&signature={signature}'
        response = requests.get(url, headers=headers, proxies=proxies)
        if not response:
            continue

        new_trades = response.json()
        assert type(new_trades) == list

        for trade in new_trades:
            if last_id == trade['id'] and last_symbol == trade['symbol']:
                continue
            BinanceTrade.create(
                symbol=trade['symbol'],
                id=str(trade['id']),
                order_id=str(trade['orderId']),
                side=trade['side'],
                position_side=trade['positionSide'],
                qty=Decimal(trade['qty']),
                price=Decimal(trade['price']),
                timestamp=datetime.fromtimestamp(trade['time'] / 1000)
            )
        if new_trades:
            last_id = new_trades[-1]['id']
            last_symbol = new_trades[-1]['symbol']
        if len(new_trades) == limit:
            start_time = new_trades[-1]['time']
        else:
            start_time += 7 * 24 * 60 * 60 * 1000


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
    url = 'https://fapi.binance.com/fapi/v1/klines'
    timestamp = round(time.time() * 1000)
    while start_time < timestamp:
        params = {
            'symbol': symbol,
            'interval': '1h',
            'limit': 1500,
            'startTime': start_time,
        }
        response = requests.get(url, params=params, proxies=proxies)
        if not response.json():
            break
        for data in response.json():
            close_price = Decimal(data[4])
            close_time = data[6]
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
