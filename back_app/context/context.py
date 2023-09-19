from playhouse.postgres_ext import PostgresqlExtDatabase

from config.local_settings import subgraph_endpoint, binance_api_key, binance_api_secret, db_port, db_host, db_password, \
    db_user, db_name
from config.settings import proxies
from context.binance_client import BinanceClient
from context.graphql_client import GraphQlClient
from utils.logger_utils import setup_peewee_logger

gc = GraphQlClient(endpoint=subgraph_endpoint, proxies=proxies)
binance_client = BinanceClient(binance_api_key, binance_api_secret, requests_params=dict(proxies=proxies))
pg_db = PostgresqlExtDatabase(db_name, user=db_user, password=db_password, host=db_host, port=db_port)
setup_peewee_logger()
