import datetime

import web3
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from web3_collections import MultiEndpointHTTPProvider

from app import log_span_context
from config.settings import ERC20_ABI, Context, SNAPSHOT_BLOCK_LAG


def load_config(session: Session, context: Context, transaction_id=None):
    from app.models import RuntimeConfiguration

    def update_endpoint(current_endpoint, next_endpoint, exception):
        if transaction_id:
            with log_span_context(session, 'Update Endpoint', transaction_id)as span:
                span.add_data('current_endpoint', f'{current_endpoint}')
                span.add_data('next_endpoint', f'{next_endpoint}')
                span.add_data('exception', f'{exception}')
        return True

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
                before_endpoint_update=update_endpoint,
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
