from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from tqdm import tqdm

from app.models import FundingRate, AccountTrade, SymbolPrice, PaidFundingRate
from config.local_settings import from_unix_timestamp
from utils.binance_utils import fetch_account_trades, fetch_symbol_price_history, fetch_funding_rate_history


def fetch_new_data():
    print(f"Paid Funding:: fetching trades")
    fetch_account_trades()
    all_trades = AccountTrade.select().order_by(AccountTrade.timestamp.asc())
    symbols = list({t.symbol for t in all_trades})

    for i in tqdm(range(len(symbols)), "Getting funding rate for symbols"):
        symbol = symbols[i]
        fetch_symbol_price_history(symbol)
        fetch_funding_rate_history(symbol)


def calculate_paid_funding():
    print('Calculate paid funding')
    fetch_new_data()

    all_trades = AccountTrade.select().order_by(AccountTrade.timestamp.asc())
    latest_paid_funding = PaidFundingRate.select().order_by(PaidFundingRate.timestamp.desc()).first()

    if latest_paid_funding:
        latest = latest_paid_funding.timestamp
    else:
        latest = datetime.fromtimestamp(from_unix_timestamp / 1000)

    funding_rates = FundingRate.select().where(FundingRate.timestamp > latest).order_by(FundingRate.timestamp.asc())

    prices = defaultdict(dict)
    for price in SymbolPrice.select().where(SymbolPrice.timestamp > latest):
        epoch = round(price.timestamp.timestamp()) * 1000
        prices[price.symbol][epoch] = price

    open_amount = defaultdict(int)
    frs = defaultdict(list)
    for fr in funding_rates:  # type: FundingRate
        epoch = round(fr.timestamp.timestamp()) * 1000
        if epoch < from_unix_timestamp:
            continue
        frs[epoch].append(fr)
    if not frs:
        return
    epochs = (e for e in sorted(frs))
    next_epoch = next(epochs)
    for trade in all_trades:  # type: AccountTrade
        while trade.timestamp.timestamp() * 1000 > next_epoch:
            for fr in frs[next_epoch]:  # type: FundingRate
                price = prices[fr.symbol].get(next_epoch)
                if price is None:
                    continue
                open_qty = open_amount[fr.symbol]
                if abs(open_qty) >= 1e-7:
                    calculated_funding_rate = fr.rate * price.price * Decimal(open_qty)
                    print(f'{fr.timestamp} - {fr.symbol} FR:', calculated_funding_rate)
                    PaidFundingRate.create(
                        symbol=fr.symbol,
                        timestamp=fr.timestamp,
                        amount=round(calculated_funding_rate * 10 ** 18),
                    )
            try:
                next_epoch = next(epochs)
            except StopIteration:
                return
        sym = trade.symbol
        if trade.position_side == 'SHORT':
            if trade.side == 'SELL':
                open_amount[sym] += float(trade.qty)
            elif trade.side == 'BUY':
                open_amount[sym] -= float(trade.qty)
            else:
                raise Exception(trade.side)
        elif trade.position_side == 'LONG':
            if trade.side == 'BUY':
                open_amount[sym] += float(trade.qty)
            elif trade.side == 'SELL':
                open_amount[sym] -= float(trade.qty)
            else:
                raise Exception(trade.side)

    remains = [next_epoch] + list(epochs)
    for next_epoch in remains:
        for fr in frs[next_epoch]:  # type: FundingRate
            price = prices[fr.symbol][next_epoch]
            open_qty = open_amount[fr.symbol]
            if abs(open_qty) >= 1e-7:
                calculated_funding_rate = fr.rate * price.price * Decimal(open_qty)
                print(f'{fr.timestamp} - {fr.symbol} FR:', calculated_funding_rate)
                PaidFundingRate.create(
                    symbol=fr.symbol,
                    timestamp=fr.timestamp,
                    amount=round(calculated_funding_rate * 10 ** 18),
                )
