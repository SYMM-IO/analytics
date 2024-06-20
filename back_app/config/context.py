from dataclasses import dataclass

from utils.binance_client import BinanceClient


@dataclass
class HedgerContextUtils:
    binance_client: BinanceClient

    @staticmethod
    def from_context(context):
        context = HedgerContextUtils(
            binance_client=BinanceClient(context.binance_api_key, context.binance_api_secret) if len(context.binance_api_key) > 0 else None,
        )
        return context
