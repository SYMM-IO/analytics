import os

import web3
from web3.middleware import geth_poa_middleware

from app import db_session
from app.models import RuntimeConfiguration
from config.local_settings import contexts
from cronjobs.snapshot.affiliate_snapshot import prepare_affiliate_snapshot
from cronjobs.snapshot.hedger_snapshot import prepare_hedger_snapshot
from services.config_service import load_config
from utils.block import Block


def get_context():
    tenant = os.environ["TENANT"]
    for context in contexts:
        if context.tenant == tenant:
            return context
    raise Exception("Invalid context")


def prepare_historical_snapshots():
    context = get_context()

    w3 = web3.Web3(web3.Web3.HTTPProvider(context.rpc))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    block = Block.latest(w3)

    while block.timestamp() > context.from_unix_timestamp:
        with db_session() as session:
            config: RuntimeConfiguration = load_config(session, context)
            if config.last_historical_snapshot_block:
                block = Block(w3, config.last_historical_snapshot_block)
            block.backward(context.historical_snapshot_step)

            print(f"{context.tenant}: Historical snapshot for block {block.number} - {block.datetime()}")
            for affiliate_context in context.affiliates:
                for hedger_context in context.hedgers:
                    prepare_affiliate_snapshot(
                        config,
                        context,
                        session,
                        affiliate_context,
                        hedger_context,
                        block,
                    )
            for hedger_context in context.hedgers:
                prepare_hedger_snapshot(config, context, session, hedger_context, block)
            config.last_historical_snapshot_block = block.number
            config.upsert(session)
