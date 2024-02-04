import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

import requests
from tqdm import tqdm

from app.models import FundingRate, BinanceTrade, SymbolPrice, PaidFundingRate
from config.settings import Context, PROXIES


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
        response = requests.post(url, json=json_data, proxies=PROXIES)
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


def fetch_new_data(context: Context):
    all_trades = (
        BinanceTrade.select()
        .where(BinanceTrade.tenant == context.tenant)
        .order_by(BinanceTrade.timestamp.asc())
    )
    symbols = list({t.symbol for t in all_trades})

    for i in tqdm(range(len(symbols)), "Getting funding rate for symbols"):
        symbol = symbols[i]
        fetch_symbol_price_history(context, symbol)
        fetch_funding_rate_history(context, symbol)


def calculate_paid_funding(context: Context):
    print("Calculate paid funding")
    fetch_new_data(context)

    all_trades = (
        BinanceTrade.select()
        .where(BinanceTrade.tenant == context.tenant)
        .order_by(BinanceTrade.timestamp.asc())
    )
    latest_paid_funding = (
        PaidFundingRate.select()
        .where(PaidFundingRate.tenant == context.tenant)
        .order_by(PaidFundingRate.timestamp.desc())
        .first()
    )

    if latest_paid_funding:
        latest = latest_paid_funding.timestamp
    else:
        latest = datetime.fromtimestamp(context.from_unix_timestamp / 1000)

    funding_rates = (
        FundingRate.select()
        .where(FundingRate.timestamp > latest)
        .order_by(FundingRate.timestamp.asc())
    )

    prices = defaultdict(dict)
    for price in SymbolPrice.select().where(SymbolPrice.timestamp > latest):
        epoch = round(price.timestamp.timestamp()) * 1000
        prices[price.symbol][epoch] = price

    open_amount = defaultdict(int)
    frs = defaultdict(list)
    for fr in funding_rates:  # type: FundingRate
        epoch = round(fr.timestamp.timestamp()) * 1000
        if epoch < context.from_unix_timestamp:
            continue
        frs[epoch].append(fr)
    if not frs:
        return
    epochs = (e for e in sorted(frs))
    next_epoch = next(epochs)
    for trade in all_trades:  # type: BinanceTrade
        while trade.timestamp.timestamp() * 1000 > next_epoch:
            for fr in frs[next_epoch]:  # type: FundingRate
                price = prices[fr.symbol].get(next_epoch)
                if price is None:
                    continue
                open_qty = open_amount[fr.symbol]
                if abs(open_qty) >= 1e-7:
                    calculated_funding_rate = fr.rate * price.price * Decimal(open_qty)
                    print(f"{fr.timestamp} - {fr.symbol} FR:", calculated_funding_rate)
                    PaidFundingRate.create(
                        tenant=context.tenant,
                        symbol=fr.symbol,
                        timestamp=fr.timestamp,
                        amount=round(calculated_funding_rate * 10**18),
                    )
            try:
                next_epoch = next(epochs)
            except StopIteration:
                return
        sym = trade.symbol
        if trade.position_side == "SHORT":
            if trade.side == "SELL":
                open_amount[sym] += float(trade.qty)
            elif trade.side == "BUY":
                open_amount[sym] -= float(trade.qty)
            else:
                raise Exception(trade.side)
        elif trade.position_side == "LONG":
            if trade.side == "BUY":
                open_amount[sym] += float(trade.qty)
            elif trade.side == "SELL":
                open_amount[sym] -= float(trade.qty)
            else:
                raise Exception(trade.side)

    remains = [next_epoch] + list(epochs)
    for next_epoch in remains:
        for fr in frs[next_epoch]:  # type: FundingRate
            symbol_prices = prices[fr.symbol]
            price = symbol_prices.get(next_epoch)
            if price is None:
                try:
                    key = next(
                        filter(lambda x: x > next_epoch, sorted(symbol_prices.keys()))
                    )
                except StopIteration:
                    try:
                        key = next(
                            filter(
                                lambda x: x < next_epoch,
                                sorted(symbol_prices.keys()),
                            )
                        )
                    except StopIteration:
                        print(
                            f"WARNING: can not find price for {fr.symbol} in time={next_epoch}"
                        )
                        continue
                price = symbol_prices[key]
            open_qty = open_amount[fr.symbol]
            if abs(open_qty) >= 1e-7:
                calculated_funding_rate = fr.rate * price.price * Decimal(open_qty)
                print(f"{fr.timestamp} - {fr.symbol} FR:", calculated_funding_rate)
                PaidFundingRate.create(
                    tenant=context.tenant,
                    symbol=fr.symbol,
                    timestamp=fr.timestamp,
                    amount=round(calculated_funding_rate * 10**18),
                )
