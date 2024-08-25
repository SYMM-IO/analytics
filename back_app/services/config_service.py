import datetime
import logging

import web3
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from web3_collections import MultiEndpointHTTPProvider

from config.settings import ERC20_ABI, Context, SNAPSHOT_BLOCK_LAG, LOGGER


def load_config(session: Session, context: Context, name: str = "DefaultConfiguration"):
    from app.models import RuntimeConfiguration

    config: RuntimeConfiguration = session.scalars(
        select(RuntimeConfiguration).where(
            and_(
                RuntimeConfiguration.name == name,
                RuntimeConfiguration.tenant == context.tenant,
            )
        )
    ).first()
    if not config:
        logger = logging.getLogger(LOGGER)
        w3 = web3.Web3(MultiEndpointHTTPProvider(
            context.rpcs,
            before_endpoint_update=lambda current_endpoint, next_endpoint, exception: logger.debug(
                f'{current_endpoint=}, {next_endpoint=}, {exception=}') or True))
        collateral_contract = w3.eth.contract(address=w3.to_checksum_address(context.symmio_collateral_address),
                                              abi=ERC20_ABI)
        decimals = collateral_contract.functions.decimals().call()
        start_time = datetime.datetime.utcfromtimestamp(context.deploy_timestamp // 1000) - datetime.timedelta(days=5)
        config = RuntimeConfiguration(name=name, decimals=decimals, tenant=context.tenant, deployTimestamp=start_time,
                                      lastSnapshotBlock=0, snapshotBlockLag=SNAPSHOT_BLOCK_LAG)
        config.save(session)
        session.flush()
    return config
