import web3
from multicallable import Multicallable
from web3.middleware import geth_poa_middleware

from app import db_session
from app.models import (
    RuntimeConfiguration,
    User,
    Symbol,
    Account,
    BalanceChange,
    Quote,
    TradeHistory,
    DailyHistory,
)
from config.settings import (
    Context,
    SNAPSHOT_BLOCK_LAG,
    SYMMIO_ABI,
)
from services.config_service import load_config
from services.snapshot.affiliate_snapshot import prepare_affiliate_snapshot
from services.snapshot.hedger_snapshot import prepare_hedger_snapshot
from services.snapshot.liquidator_snapshot import prepare_liquidator_snapshot
from services.snapshot.snapshot_context import SnapshotContext
from utils.block import Block
from utils.subgraph.subgraph_client import SubgraphClient


async def fetch_snapshot(context: Context):
    with db_session() as session:
        w3 = web3.Web3(web3.Web3.HTTPProvider(context.rpc))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        multicallable = Multicallable(w3.to_checksum_address(context.symmio_address), SYMMIO_ABI, w3)

        config: RuntimeConfiguration = load_config(session, context)
        snapshot_context = SnapshotContext(context, session, config, w3, multicallable)
        snapshot_block = Block.latest(w3)
        snapshot_block.backward(SNAPSHOT_BLOCK_LAG)

        session.commit()
        SubgraphClient(context, User).sync(session, snapshot_block)
        SubgraphClient(context, Symbol).sync(session, snapshot_block)
        SubgraphClient(context, Account).sync(session, snapshot_block)
        SubgraphClient(context, BalanceChange).sync(session, snapshot_block)
        SubgraphClient(context, Quote).sync(session, snapshot_block)
        SubgraphClient(context, TradeHistory).sync(session, snapshot_block)
        SubgraphClient(context, DailyHistory).sync(session, snapshot_block)

        config.lastSnapshotBlock = snapshot_block.number
        config.upsert(session)

        session.commit()

        print(f"{context.tenant}: Data loaded...\nPreparing snapshots...")

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
