import datetime

import web3
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from web3_collections import MultiEndpointHTTPProvider

from config.settings import ERC20_ABI, Context, SNAPSHOT_BLOCK_LAG


def load_config(session: Session, context: Context):
    from app.models import RuntimeConfiguration

    config: RuntimeConfiguration = session.scalars(
        select(RuntimeConfiguration).where(
            and_(
                RuntimeConfiguration.tenant == context.tenant,
            )
        )
    ).first()
    if not config:
        w3 = web3.Web3(
            MultiEndpointHTTPProvider(
                context.rpcs,
                before_endpoint_update=None  # fixme: comment code below
            )
        )
        collateral_contract = w3.eth.contract(address=w3.to_checksum_address(context.symmio_collateral_address),
                                              abi=ERC20_ABI)
        decimals = collateral_contract.functions.decimals().call()
        start_time = datetime.datetime.utcfromtimestamp(context.deploy_timestamp // 1000) - datetime.timedelta(days=5)
        config = RuntimeConfiguration(
            decimals=decimals, tenant=context.tenant, deployTimestamp=start_time, lastSnapshotBlock=0,
            snapshotBlockLag=SNAPSHOT_BLOCK_LAG
        )
        config.upsert(session)
        session.flush()
    return config


"""
lambda current_endpoint, next_endpoint, exception: logger.debug(
                    f"{current_endpoint=}, {next_endpoint=}, {exception=}"
                )
                or True,
"""
