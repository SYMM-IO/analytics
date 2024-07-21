from dataclasses import dataclass

from config.local_settings import fallback_binance_api_key, fallback_binance_api_secret
from utils.binance_client import BinanceClient


@dataclass
class HedgerContextUtils:
    binance_client: BinanceClient

    @staticmethod
    def from_context(context):
        context = HedgerContextUtils(
            binance_client=BinanceClient(context.binance_api_key, context.binance_api_secret)
            if len(context.binance_api_key) > 0
            else BinanceClient(fallback_binance_api_key, fallback_binance_api_secret),
        )
        return context
