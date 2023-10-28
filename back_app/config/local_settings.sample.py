import json

subgraph_endpoint = ''
rpc = ''
hedger_address = ''
hedger_max_open_interest_ratio = 20
symmio_address = ''
symmio_collateral_address = ''
symmio_liquidators = []
symmio_multi_account = ''

with open('./config/abis/abi.json', 'r') as f:
    symmio_abi = json.load(f)

binance_api_key = ""
binance_api_secret = ""
binance_email = ""
binance_is_master = True

telegram_group_id = ''
telegram_error_group_id = ''
telegram_bot_token = ''
telegram_api_auth_token = ''

admin_api_key = ""

db_name = "postgres"
db_user = "postgres"
db_password = "password"
db_host = "localhost"
db_port = 5432

deposit_diff = 0
from_unix_timestamp = 1677529800000

mention_for_red_alert_accounts = []
mention_cooldown = 10 * 60