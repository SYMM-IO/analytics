import json
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import load_only
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3_collections import MultiEndpointHTTPProvider

from app import db_session
from app.models import BalanceChange
from config.contexts.blast_8_2 import blast_8_2_contexts

DEC18 = 10 ** 18
w3 = Web3(MultiEndpointHTTPProvider(blast_8_2_contexts.rpcs))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
with open('config/abis/erc20abi.json', 'r') as fp:
    abi = json.load(fp)
usdb_contract = w3.eth.contract(address=w3.to_checksum_address(blast_8_2_contexts.symmio_collateral_address), abi=abi)
balance = usdb_contract.functions.balanceOf(w3.to_checksum_address(blast_8_2_contexts.symmio_address)).call()
print('balance:', balance / DEC18)
deposit = 0
withdraw = 0
with db_session() as session:
    balance_changes: List[BalanceChange] = session.scalars(
        select(BalanceChange).where(BalanceChange.tenant == 'BLAST_8_2').options(
            load_only(
                BalanceChange.amount,
                BalanceChange.type,
            )))
    for balance_change in balance_changes:
        if balance_change.type == 'DEPOSIT':
            deposit += balance_change.amount
            balance -= balance_change.amount
        elif balance_change.type == 'WITHDRAW':
            withdraw += balance_change.amount
            balance += balance_change.amount
print('deposit:', deposit / DEC18)
print('withdraw:', withdraw / DEC18)
print('mint:', balance / DEC18)
