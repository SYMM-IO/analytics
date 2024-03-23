import datetime
import time

from web3 import Web3


class Block:
    def __init__(self, w3: Web3, block_number: int):
        self.number = block_number
        self.w3 = w3
        self.block = self.w3.eth.get_block(block_number)

    @staticmethod
    def latest(w3: Web3):
        latest_block = w3.eth.get_block("latest")
        return Block(w3, latest_block.get("number"))

    def timestamp(self) -> int:
        return self.block["timestamp"]

    def datetime(self) -> datetime.datetime:
        return datetime.datetime.utcfromtimestamp(self.timestamp())

    def is_for_past(self):
        return self.timestamp() < time.time() - (60 * 10)
