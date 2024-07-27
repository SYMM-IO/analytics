import requests
from sqlalchemy import select, and_

from app.models import GasHistory
from config.settings import Context, HedgerContext
from services.snapshot.snapshot_context import SnapshotContext


def fetch_native_transferred(context: Context, w3, wallet_address, initial_block=0, page_size=10000):
    tx_count = 0
    value_transferred = w3.eth.get_balance(w3.to_checksum_address(wallet_address), block_identifier=initial_block)
    current_balance = w3.eth.get_balance(w3.to_checksum_address(wallet_address))
    from_block = initial_block
    to_block = w3.eth.get_block("latest").get("number")

    while True:
        url = (
            f"{context.explorer}/api?module=account&action=txlist&address={wallet_address}"
            f"&startblock={from_block}&endblock={to_block}&sort=asc&page=1&offset={page_size}"
            f"&apikey={context.explorer_api_key}"
        )
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(f"Error fetching transactions for wallet {wallet_address}")

        data = response.json()

        if data["status"] == "0":
            if data["message"] == "No transactions found":
                print(f"All transactions fetched for wallet {wallet_address}")
                break

            raise Exception(f"Error fetching transactions for wallet {wallet_address}, ")

        transactions = data["result"]
        tx_count += len(transactions)
        for tx in transactions:
            value, to_, from_ = int(tx["value"]), tx["to"], tx["from"]
            if value == 0 or to_ == "":
                continue
            to_, from_ = w3.to_checksum_address(to_), w3.to_checksum_address(from_)
            if from_ != wallet_address and to_ == wallet_address:
                value_transferred += value
            if to_ != wallet_address and from_ == wallet_address:
                value_transferred -= value

        if len(transactions) < page_size:
            print(f"All transactions fetched for wallet {wallet_address}")
            break

        from_block = int(transactions[-1]["blockNumber"]) + 1
    return tx_count, value_transferred - current_balance, to_block


def gas_used_by_hedger_wallets(snapshot_context: SnapshotContext, hedger_context: HedgerContext):
    total_gas_spent_by_all_wallets = 0
    for address in hedger_context.wallets:
        record: GasHistory = snapshot_context.session.scalar(select(GasHistory).where(
            and_(GasHistory.address == address, GasHistory.tenant == snapshot_context.context.tenant)))
        if record:
            tx_count, gas_used, last_block = fetch_native_transferred(snapshot_context.context,
                                                                      snapshot_context.context.w3, address,
                                                                      record.initial_block)
            record.tx_count += tx_count
            record.gas_amount += gas_used
            record.initial_block = last_block
        else:
            tx_count, gas_used, last_block = fetch_native_transferred(snapshot_context.context,
                                                                      snapshot_context.context.w3, address)
            record = GasHistory(address=address, gas_amount=gas_used, initial_block=last_block, tx_count=tx_count,
                                tenant=snapshot_context.context.tenant)
            record.save(snapshot_context.session)
        print(f"Loaded {record.tx_count} transactions for wallet {address} with total gas of",
              snapshot_context.context.w3.from_wei(record.gas_amount, 'ether'))
        snapshot_context.session.commit()
        total_gas_spent_by_all_wallets += record.gas_amount
    return snapshot_context.context.w3.from_wei(total_gas_spent_by_all_wallets, 'ether')
