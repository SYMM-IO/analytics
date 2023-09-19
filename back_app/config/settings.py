import json

proxies = {}
# proxies = {'http': 'socks5h://127.0.0.1:9999', 'https': 'socks5h://127.0.0.1:9999'}
fetch_data_interval = 10
funding_fetch_data_interval = 10
update_binance_deposit_interval = 20
server_port = 7231

with open('./config/abis/erc20abi.json', 'r') as f:
    erc20_abi = json.load(f)
