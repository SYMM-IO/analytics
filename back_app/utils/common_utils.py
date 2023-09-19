import datetime

import web3

from config.local_settings import rpc, symmio_collateral_address
from config.settings import erc20_abi


def load_config(name: str = "DefaultConfiguration"):
    from app.models import RuntimeConfiguration

    try:
        config = RuntimeConfiguration.get(name=name)
    except:
        w3 = web3.Web3(web3.Web3.HTTPProvider(rpc))
        collateral_contract = w3.eth.contract(address=w3.to_checksum_address(symmio_collateral_address), abi=erc20_abi)
        decimals = collateral_contract.functions.decimals().call()
        config = RuntimeConfiguration.create(binanceDeposit=0, decimals=decimals, name=name,
                                             deployTimestamp=datetime.datetime.utcnow() - datetime.timedelta(days=300))
        config.save()
    return config


def convert_timestamps(data):
    output = {}
    for key, value in data.items():
        if "timestamp" in key.lower():
            output[key] = datetime.datetime.fromtimestamp(int(value))
        else:
            output[key] = value
    return output
