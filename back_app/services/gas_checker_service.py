import requests
from sqlalchemy import select, and_

from app import log_span_context
from app.models import GasHistory
from config.settings import HedgerContext
from services.snapshot.snapshot_context import SnapshotContext
from utils.model_utils import log_object_properties


def fetch_native_transferred(snapshot_context: SnapshotContext, wallet_address, to_block, transaction_id,
                             initial_block=0):
    with log_span_context(snapshot_context.session, "Fetch Native Transferred", transaction_id) as log_span:
        page_size = 10000
        tx_count = 0
        from_block = initial_block
        explorer_api_keys = 3 * snapshot_context.context.explorer_api_keys.copy()
        value_transferred = snapshot_context.context.w3.eth.get_balance(
            snapshot_context.context.w3.to_checksum_address(wallet_address), block_identifier=initial_block
        )
        current_balance = snapshot_context.context.w3.eth.get_balance(
            snapshot_context.context.w3.to_checksum_address(wallet_address), block_identifier=to_block
        )
        log_span.add_data("fetch_native_transferred", f'{wallet_address=}')
        log_span.add_data("fetch_native_transferred", f'{to_block=}')
        log_span.add_data("fetch_native_transferred", f'{page_size=}')
        while explorer_api_keys:
            url = (
                f"{snapshot_context.context.explorer}/api?module=account&action=txlist&address={wallet_address}"
                f"&startblock={from_block}&endblock={to_block}&sort=asc&page=1&offset={page_size}"
                f"&apikey={explorer_api_keys[0]}"
            )
            response = requests.get(url)

            log_span.add_data("fetch_native_transferred", f'{from_block=}')
            log_span.add_data("fetch_native_transferred", f'{explorer_api_keys[0]=}')
            if response.status_code != 200:
                log_span.add_data("fetch_native_transferred", f'{response.status_code=}')
                explorer_api_keys.pop(0)
                continue

            data = response.json()

            if data["status"] == "0":
                if data["message"] == "No transactions found":
                    print(f"All transactions fetched for wallet {wallet_address}")
                    break
                log_span.add_data("fetch_native_transferred", f'{data["message"]=}')
                log_span.add_data("fetch_native_transferred", f'{data["result"]=}')
                explorer_api_keys.pop(0)
                continue

            transactions = data["result"]
            tx_count += len(transactions)
            for tx in transactions:
                value, to_, from_ = int(tx["value"]), tx["to"].lower(), tx["from"].lower()
                if value == 0 or to_ == "":
                    continue
                if from_ != wallet_address and to_ == wallet_address:
                    value_transferred += value
                if to_ != wallet_address and from_ == wallet_address:
                    value_transferred -= value

            if len(transactions) < page_size:
                print(f"All transactions fetched for wallet {wallet_address}")
                break

            from_block = int(transactions[-1]["blockNumber"]) + 1
        else:
            raise Exception(f"Error fetching transactions for wallet {wallet_address} (All api keys failed)")

    return tx_count, value_transferred - current_balance


def gas_used_by_hedger_wallets(snapshot_context: SnapshotContext, hedger_context: HedgerContext, last_block,
                               transaction_id):
    with log_span_context(snapshot_context.session, "Gas Used By Hedger Wallets", transaction_id) as log_span:
        total_gas_spent_by_all_wallets = 0
        for address in hedger_context.wallets:
            gas_history: GasHistory = snapshot_context.session.scalar(
                select(GasHistory).where(
                    and_(GasHistory.address == address, GasHistory.tenant == snapshot_context.context.tenant))
            )
            gas_history_details = log_object_properties(gas_history)
            log_span.add_data("gas_used_by_hedger_wallets", gas_history_details)
            if gas_history:
                if last_block > gas_history.initial_block:
                    tx_count, gas_used = fetch_native_transferred(snapshot_context, address, last_block, transaction_id,
                                                                  gas_history.initial_block)
                    gas_history.tx_count += tx_count
                    gas_history.gas_amount += gas_used
                    gas_history.initial_block = last_block + 1
            else:
                tx_count, gas_used = fetch_native_transferred(snapshot_context, address, last_block, transaction_id)
                gas_history = GasHistory(
                    address=address, gas_amount=gas_used, initial_block=last_block, tx_count=tx_count,
                    tenant=snapshot_context.context.tenant
                )
                gas_history.upsert(snapshot_context.session)
            log_span.add_data("gas_used_by_hedger_wallets", gas_history.gas_amount)
            print(
                f"Loaded {gas_history.tx_count} transactions for wallet {address} with total gas of",
                snapshot_context.context.w3.from_wei(gas_history.gas_amount, "ether"),
            )
            total_gas_spent_by_all_wallets += gas_history.gas_amount
            gas_history_details = log_object_properties(gas_history)
            log_span.add_data("gas_used_by_hedger_wallets", gas_history_details)
            log_span.add_data("gas_used_by_hedger_wallets", total_gas_spent_by_all_wallets)
    return snapshot_context.context.w3.from_wei(total_gas_spent_by_all_wallets, "ether")
