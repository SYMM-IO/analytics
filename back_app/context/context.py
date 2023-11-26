from dataclasses import dataclass

from context.binance_client import BinanceClient
from context.graphql_client import GraphQlClient


@dataclass
class ContextUtils:
	gc: GraphQlClient
	binance_client: BinanceClient

	@staticmethod
	def from_configuration(context):
		context = ContextUtils(
			gc=GraphQlClient(endpoint=context.subgraph_endpoint),
			binance_client=BinanceClient(context.binance_api_key, context.binance_api_secret)
		)
		return context
