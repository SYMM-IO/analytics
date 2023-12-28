import datetime

import web3

from config.settings import ERC20_ABI, Context


def load_config(context: Context, name: str = "DefaultConfiguration"):
    from app.models import RuntimeConfiguration

    try:
        config = RuntimeConfiguration.get(name=name, tenant=context.tenant)
    except:
        w3 = web3.Web3(web3.Web3.HTTPProvider(context.rpc))
        collateral_contract = w3.eth.contract(
            address=w3.to_checksum_address(context.symmio_collateral_address),
            abi=ERC20_ABI,
        )
        decimals = collateral_contract.functions.decimals().call()
        config = RuntimeConfiguration.create(
            binanceDeposit=0,
            decimals=decimals,
            name=name,
            tenant=context.tenant,
            deployTimestamp=datetime.datetime.utcnow() - datetime.timedelta(days=300),
        )
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
