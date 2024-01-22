import csv
from typing import List

from app.models import BalanceChange, BinanceIncome
from config.local_settings import contexts
from config.settings import Context
from services.config_service import load_config


def write_balance_changes(
    context: Context, writer, _balance_changes: List[BalanceChange], account_type: str
):
    conf = load_config(context)
    for item in _balance_changes:
        item: BalanceChange
        human_readable_timestamp = item.timestamp.strftime("%m-%d-%Y %H:%M")
        writer.writerow(
            [
                item.transaction,
                human_readable_timestamp,
                int(item.amount) / (10**conf.decimals),
                item.type,
                f"Contract {context.tenant}",
                account_type,
            ]
        )


def write_incomes(context: Context, writer, _incomes: List[BinanceIncome]):
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
                "",
            ]
        )


def get_rebalance_report():
    with open(f"rebalance.csv", "w", newline="") as file:
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
        for context in contexts:
            print(f"Going for {context.tenant}")
            for hedger in context.hedgers:
                balance_changes = (
                    BalanceChange.select()
                    .where(
                        BalanceChange.collateral == context.symmio_collateral_address,
                        BalanceChange.account == hedger.hedger_address,
                        BalanceChange.tenant == context.tenant,
                    )
                    .order_by(BalanceChange.timestamp)
                )
                print(f"Found {len(balance_changes)} hedger balance changes")
                write_balance_changes(context, writer, balance_changes, "Hedger")
            for affiliate in context.affiliates:
                for liq in affiliate.symmio_liquidators:
                    balance_changes = (
                        BalanceChange.select()
                        .where(
                            BalanceChange.collateral
                            == context.symmio_collateral_address,
                            BalanceChange.account == liq,
                            BalanceChange.tenant == context.tenant,
                        )
                        .order_by(BalanceChange.timestamp)
                    )
                    write_balance_changes(
                        context, writer, balance_changes, "Liquidator"
                    )
                incomes = (
                    BinanceIncome.select()
                    .where(
                        BinanceIncome.tenant == context.tenant,
                        BinanceIncome.type == BinanceIncome.type == "TRANSFER",
                    )
                    .order_by(BinanceIncome.timestamp)
                )
                write_incomes(context, writer, incomes)


get_rebalance_report()
