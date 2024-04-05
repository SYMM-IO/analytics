import time
from functools import wraps

from binance.client import Client


def handle_rec_window(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs["timestamp"] = int(time.time() * 1000)
        kwargs["recvWindow"] = 60000
        return func(*args, **kwargs)

    return wrapper


class BinanceClient(Client):
    @handle_rec_window
    def futures_account(self, **params):
        return super().futures_account(**params)

    @handle_rec_window
    def futures_position_information(self, **params):
        return super().futures_position_information(**params)

    @handle_rec_window
    def futures_mark_price(self, **params):
        return super().futures_mark_price(**params)

    @handle_rec_window
    def futures_income_history(self, **params):
        return super().futures_income_history(**params)
