from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from tqdm import tqdm

from app.models import FundingRate, BinanceTrade, SymbolPrice, PaidFundingRate
from config.settings import Context
from utils.binance_utils import fetch_symbol_price_history, fetch_funding_rate_history


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
