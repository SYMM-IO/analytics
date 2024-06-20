from decimal import Decimal

from sqlalchemy import select, func, and_

from app.models import BalanceChange, BalanceChangeType, LiquidatorSnapshot
from services.snapshot.snapshot_context import SnapshotContext
from utils.block import Block


def prepare_liquidator_snapshot(snapshot_context: SnapshotContext, liquidator: str, snapshot_block: Block):
    account_withdraw = snapshot_context.session.scalar(
        select(func.sum(BalanceChange.amount)).where(
            and_(
                BalanceChange.collateral == snapshot_context.context.symmio_collateral_address,
                BalanceChange.type == BalanceChangeType.WITHDRAW,
                BalanceChange.account_id == liquidator,
                BalanceChange.blockNumber <= snapshot_block.number,
                BalanceChange.tenant == snapshot_context.context.tenant,
            )
        )
    ) or Decimal(0)

    LiquidatorSnapshot(
        address=liquidator,
        withdraw=int(account_withdraw) * 10 ** (18 - snapshot_context.config.decimals),
        balance=snapshot_context.multicallable.balanceOf([snapshot_context.w3.to_checksum_address(liquidator)]).call(
            block_identifier=snapshot_block.number
        )[0],
        allocated=snapshot_context.multicallable.balanceInfoOfPartyA([snapshot_context.w3.to_checksum_address(liquidator)]).call(
            block_identifier=snapshot_block.number
        )[0][0],
    ).save(session=snapshot_context.session)
