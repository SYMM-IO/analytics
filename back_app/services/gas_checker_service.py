import requests

from config.settings import Context, HedgerContext
from services.snapshot.snapshot_context import SnapshotContext


def fetch_native_transferred(context: Context, w3, wallet_address, initial_block=0, page_size=10000):
    tx_count = 0
    value_transferred = 0
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
    return tx_count, w3.from_wei(value_transferred - current_balance, "ether")


def gas_used_by_hedger_wallets(snapshot_context: SnapshotContext, hedger_context: HedgerContext):
    total_gas_spent_by_all_wallets = 0
    for address in hedger_context.wallets:
        tx_count, gas_used = fetch_native_transferred(snapshot_context.context, snapshot_context.w3, address)
        print(f"Loaded {tx_count} transactions for wallet {address} with total gas of {gas_used}")
        total_gas_spent_by_all_wallets += gas_used
    return total_gas_spent_by_all_wallets
