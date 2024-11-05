import json

from sqlalchemy import select, func
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3_collections import MultiEndpointHTTPProvider

from src.app import db_session
from src.app.subgraph_models import BalanceChange
from src.config import blast_8_2_contexts

DEC18 = 10**18
w3 = Web3(MultiEndpointHTTPProvider(blast_8_2_contexts.rpcs))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
with open("config/abis/erc20abi.json", "r") as fp:
    abi = json.load(fp)
usdb_contract = w3.eth.contract(address=w3.to_checksum_address(blast_8_2_contexts.symmio_collateral_address), abi=abi)
balance = usdb_contract.functions.balanceOf(w3.to_checksum_address(blast_8_2_contexts.symmio_address)).call()
with db_session() as session:
    deposit = session.scalar(select(func.sum(BalanceChange.amount)).where(BalanceChange.type == "DEPOSIT"))
    withdraw = session.scalar(select(func.sum(BalanceChange.amount)).where(BalanceChange.type == "WITHDRAW"))
print("balance:", balance / DEC18)
print("deposit:", deposit / DEC18)
print("withdraw:", withdraw / DEC18)
print("mint:", (balance - deposit + withdraw) / DEC18)
