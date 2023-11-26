import time
from datetime import datetime
from decimal import Decimal

from peewee import fn

from app.models import BinanceTrade
from config.settings import Context


def fetch_and_save_all_trades(context: Context, trades_start_time, period=7 * 24 * 60 * 60 * 1000):
	seen_ids = set()  # to keep track of unique trades based on ID

	start_time = trades_start_time
	now = time.time() * 1000
	while True:
		if now < start_time:
			break
		end_time = start_time + period
		end_time = min(end_time, now)
		print(f"Loading binance trades between: start_time={start_time}, end_time={end_time}")
		current_trades = context.utils.binance_client.futures_account_trades(limit=1000, startTime=int(start_time),
																			 endTime=int(end_time))
		if not current_trades:
			start_time += period
			continue

		# Add to all_trades only if the ID is not seen
		for trade in current_trades:
			if trade['id'] not in seen_ids:
				seen_ids.add(trade['id'])
				BinanceTrade(
					tenant=context.tenant,
					symbol=trade['symbol'],
					id=str(trade['id']),
					order_id=str(trade['orderId']),
					side=trade['side'],
					position_side=trade['positionSide'],
					qty=Decimal(trade['qty']),
					price=Decimal(trade['price']),
					timestamp=datetime.utcfromtimestamp(trade['time'] / 1000),
				).upsert()

		# If we got 1000 trades, the period might be too long. Halve it and continue.
		if len(current_trades) == 1000:
			period //= 2
			continue

		# If less than 1000 trades, move the startTime forward by the current period.
		start_time += period


def calculate_binance_trade_volume(context: Context):
	last_bt = BinanceTrade.select(BinanceTrade.timestamp).where(BinanceTrade.tenant == context.tenant).order_by(
		BinanceTrade.timestamp.desc()).first()
	if last_bt:
		start_time = datetime.timestamp(last_bt.timestamp) * 1000 + 1000
	else:
		start_time = context.from_unix_timestamp
	fetch_and_save_all_trades(context, start_time)
	return BinanceTrade.select(fn.SUM(BinanceTrade.price * BinanceTrade.qty)).where(
		BinanceTrade.tenant == context.tenant).scalar() or 0
