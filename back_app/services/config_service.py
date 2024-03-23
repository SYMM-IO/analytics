import datetime

import web3
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from config.settings import ERC20_ABI, Context


def load_config(session: Session, context: Context, name: str = "DefaultConfiguration"):
    from app.models import RuntimeConfiguration

    try:
        config = session.execute(
            select(RuntimeConfiguration).where(
                and_(
                    RuntimeConfiguration.name == name,
                    RuntimeConfiguration.tenant == context.tenant,
                )
            )
        ).scalar_one()
        session.expunge(config)
    except Exception:
        w3 = web3.Web3(web3.Web3.HTTPProvider(context.rpc))
        collateral_contract = w3.eth.contract(
            address=w3.to_checksum_address(context.symmio_collateral_address),
            abi=ERC20_ABI,
        )
        decimals = collateral_contract.functions.decimals().call()
        start_time = datetime.datetime.utcfromtimestamp(context.deploy_timestamp) - datetime.timedelta(days=10)
        config = RuntimeConfiguration(
            decimals=decimals,
            name=name,
            tenant=context.tenant,
            deployTimestamp=start_time,
            lastSnapshotTimestamp=start_time,
        )
        config.save(session)
        session.flush()
    return config
