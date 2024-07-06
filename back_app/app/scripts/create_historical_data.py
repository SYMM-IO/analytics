import os

import web3
from multicallable import Multicallable
from web3.middleware import geth_poa_middleware

from app import db_session
from app.models import RuntimeConfiguration
from config.local_settings import contexts
from config.settings import SYMMIO_ABI
from services.config_service import load_config
from services.snapshot.affiliate_snapshot import prepare_affiliate_snapshot
from services.snapshot.hedger_snapshot import prepare_hedger_snapshot
from services.snapshot.liquidator_snapshot import prepare_liquidator_snapshot
from services.snapshot.snapshot_context import SnapshotContext
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
    multicallable = Multicallable(w3.to_checksum_address(context.symmio_address), SYMMIO_ABI, w3)
    snapshot_block = Block.latest(w3)

    while snapshot_block.timestamp() > context.from_unix_timestamp:
        with db_session() as session:
            config: RuntimeConfiguration = load_config(session, context)
            snapshot_context = SnapshotContext(context, session, config, w3, multicallable)

            if config.lastHistoricalSnapshotBlock:
                snapshot_block = Block(w3, config.lastHistoricalSnapshotBlock)
            snapshot_block.backward(context.historical_snapshot_step)

            print(f"{context.tenant}: Historical snapshot for snapshot_block {snapshot_block.number} - {snapshot_block.datetime()}")

            for affiliate_context in context.affiliates:
                for hedger_context in context.hedgers:
                    prepare_affiliate_snapshot(
                        snapshot_context,
                        affiliate_context,
                        hedger_context,
                        snapshot_block,
                    )
                    session.commit()

            for liquidator in context.liquidators:
                prepare_liquidator_snapshot(snapshot_context, liquidator, snapshot_block)

            for hedger_context in context.hedgers:
                prepare_hedger_snapshot(snapshot_context, hedger_context, snapshot_block)
                # if hedger_context.utils.binance_client:
                #     fetch_binance_income_histories(snapshot_context, hedger_context)
                #     prepare_hedger_binance_snapshot(snapshot_context, hedger_context, snapshot_block)

            config.lastHistoricalSnapshotBlock = snapshot_block.number
            config.upsert(session)
