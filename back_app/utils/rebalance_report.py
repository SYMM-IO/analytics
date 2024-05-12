import csv
from typing import List

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app import db_session
from app.models import BalanceChange, BinanceIncome
from config.local_settings import contexts
from config.settings import Context
from services.config_service import load_config


def write_balance_changes(session: Session, context: Context, writer, _balance_changes: List[BalanceChange], account_type: str):
    conf = load_config(session, context)
    for item in _balance_changes:
        item: BalanceChange
        human_readable_timestamp = item.timestamp.strftime("%m-%d-%Y %H:%M")
        writer.writerow(
            [
                item.transaction,
                human_readable_timestamp,
                int(item.amount) / (10 ** conf.decimals),
                item.type,
                f"Contract {context.tenant}",
                account_type,
            ]
        )


def write_incomes(context: Context, writer, _incomes: List[BinanceIncome], account_type: str):
    for item in _incomes:
        item: BinanceIncome
        human_readable_timestamp = item.timestamp.strftime("%m-%d-%Y %H:%M")
        writer.writerow(
            [
                "",
                human_readable_timestamp,
                int(item.amount),
                item.type,
                f"Binance {context.tenant}",
                account_type,
            ]
        )


def get_rebalance_report( ):
    with open("rebalance.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "Transaction",
                "Timestamp",
                "Amount",
                "Type",
                "Destination/Source",
                "Account Type",
            ]
        )
        with db_session() as session:
            for context in contexts:
                print(f"Going for {context.tenant}")
                for hedger in context.hedgers:
                    balance_changes = session.scalars(
                        select(BalanceChange)
                        .where(
                            and_(
                                BalanceChange.collateral == context.symmio_collateral_address,
                                BalanceChange.account_id == hedger.hedger_address,
                                BalanceChange.tenant == context.tenant,
                            )
                        )
                        .order_by(BalanceChange.timestamp)
                    ).all()
                    print(f"Found {len(balance_changes)} hedger balance changes")
                    write_balance_changes(session, context, writer, balance_changes, hedger.name)

                    incomes = (
                        session.execute(
                            select(BinanceIncome)
                            .where(
                                and_(
                                    BinanceIncome.tenant == context.tenant,
                                    or_(
                                        BinanceIncome.type == "TRANSFER",
                                        BinanceIncome.type == "INTERNAL_TRANSFER",
                                    ),
                                    BinanceIncome.asset == "USDT",
                                    BinanceIncome.hedger == hedger.name,
                                )
                            )
                            .order_by(BinanceIncome.timestamp)
                        )
                        .scalars()
                        .all()
                    )
                    write_incomes(context, writer, incomes, hedger.name)

                liquidators = set()
                for affiliate in context.affiliates:
                    liquidators.update(affiliate.symmio_liquidators)
                for liq in liquidators:
                    balance_changes = (
                        session.execute(
                            select(BalanceChange)
                            .where(
                                and_(
                                    BalanceChange.collateral == context.symmio_collateral_address,
                                    BalanceChange.account_id == liq,
                                    BalanceChange.tenant == context.tenant,
                                )
                            )
                            .order_by(BalanceChange.timestamp)
                        )
                        .scalars()
                        .all()
                    )
                    write_balance_changes(session, context, writer, balance_changes, "Liquidator")


get_rebalance_report()
