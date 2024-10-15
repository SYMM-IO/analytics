from decimal import Decimal

from multicallable import Multicallable
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from src.app import log_span_context
from src.app.models import (
    BalanceChange,
    BalanceChangeType,
    HedgerSnapshot,
    RuntimeConfiguration,
    Quote,
)
from src.config.settings import (
    Context,
    SYMMIO_ABI,
    HedgerContext,
)
from src.services.gas_checker_service import gas_used_by_hedger_wallets
from src.services.snaphshot_service import get_last_affiliate_snapshot_for
from src.services.snapshot.snapshot_context import SnapshotContext
from src.utils.attr_dict import AttrDict
from src.utils.block import Block
from src.utils.model_utils import log_object_properties


def prepare_hedger_snapshot(snapshot_context: SnapshotContext, hedger_context: HedgerContext, block: Block, transaction_id):
    print(f"----------------Prepare Hedger Snapshot Of {hedger_context.name}")
    context: Context = snapshot_context.context
    session: Session = snapshot_context.session
    config: RuntimeConfiguration = snapshot_context.config

    snapshot = AttrDict()
    snapshot.gas = gas_used_by_hedger_wallets(snapshot_context, hedger_context, block.number, transaction_id)
    print(f"Total gas spent by all wallets of {hedger_context.name}: {snapshot.gas}")

    snapshot.users_paid_funding_fee = session.execute(
        select(func.coalesce(func.sum(Quote.userReceivedFunding), Decimal(0))).where(
            and_(
                Quote.blockNumber <= block.number,
                Quote.partyB == hedger_context.hedger_address,
                Quote.tenant == context.tenant,
            )
        )
    ).scalar_one()

    snapshot.users_received_funding_fee = session.execute(
        select(func.coalesce(func.sum(Quote.userPaidFunding), Decimal(0))).where(
            and_(
                Quote.blockNumber <= block.number,
                Quote.partyB == hedger_context.hedger_address,
                Quote.tenant == context.tenant,
            )
        )
    ).scalar_one()

    contract_multicallable = Multicallable(
        snapshot_context.context.w3.to_checksum_address(context.symmio_address), SYMMIO_ABI, snapshot_context.context.w3
    )

    snapshot.hedger_contract_balance = contract_multicallable.balanceOf(
        [snapshot_context.context.w3.to_checksum_address(hedger_context.hedger_address)]
    ).call(block_identifier=block.number)[0]

    hedger_deposit = session.execute(
        select(func.coalesce(func.sum(BalanceChange.amount), Decimal(0))).where(
            and_(
                BalanceChange.collateral == context.symmio_collateral_address,
                BalanceChange.type == BalanceChangeType.DEPOSIT,
                BalanceChange.account_id == hedger_context.hedger_address,
                BalanceChange.tenant == context.tenant,
                BalanceChange.blockNumber <= block.number,
            )
        )
    ).scalar_one()

    snapshot.hedger_contract_deposit = hedger_deposit * 10 ** (18 - config.decimals) + hedger_context.contract_deposit_diff

    hedger_withdraw = session.execute(
        select(func.coalesce(func.sum(BalanceChange.amount), Decimal(0))).where(
            and_(
                BalanceChange.collateral == context.symmio_collateral_address,
                BalanceChange.type == BalanceChangeType.WITHDRAW,
                BalanceChange.account_id == hedger_context.hedger_address,
                BalanceChange.tenant == context.tenant,
                BalanceChange.blockNumber <= block.number,
            )
        )
    ).scalar_one()

    snapshot.hedger_contract_withdraw = hedger_withdraw * 10 ** (18 - config.decimals)

    affiliates_snapshots = []
    for affiliate in context.affiliates:
        s = get_last_affiliate_snapshot_for(context, session, affiliate.name, hedger_context.name, block)
        if s:
            affiliates_snapshots.append(s)

    snapshot.contract_profit = (
        snapshot.hedger_contract_balance
        + sum([snapshot.hedger_contract_allocated for snapshot in affiliates_snapshots])
        + sum([snapshot.hedger_upnl for snapshot in affiliates_snapshots])
        - snapshot.hedger_contract_deposit
        + snapshot.hedger_contract_withdraw
    )

    snapshot.earned_cva = sum([snapshot.earned_cva for snapshot in affiliates_snapshots])
    snapshot.loss_cva = sum([snapshot.loss_cva for snapshot in affiliates_snapshots])

    snapshot.timestamp = block.datetime()
    snapshot.name = hedger_context.name
    snapshot.tenant = context.tenant
    snapshot.block_number = block.number
    hedger_snapshot = HedgerSnapshot(**snapshot)
    with log_span_context(session, "Prepare Hedger Snapshot", transaction_id) as log_span:
        hedger_snapshot_details = log_object_properties(hedger_snapshot)
        log_span.add_data("hedger_snapshot", hedger_snapshot_details)
    hedger_snapshot.save(session)
    return hedger_snapshot
