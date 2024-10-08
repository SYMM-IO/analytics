import datetime

from web3 import Web3


class Block:
    def __init__(self, w3: Web3, block_number: int, block=None):
        self.number = block_number
        self.w3 = w3
        self.block = self.load_block() if not block else block

    def load_block(self):
        return self.w3.eth.get_block(self.number)

    @staticmethod
    def latest(w3: Web3):
        latest_block = w3.eth.get_block("latest")
        return Block(w3, latest_block.get("number"), latest_block)

    def backward(self, offset: int):
        self.number = self.number - offset
        self.block = self.load_block()
        return self

    def timestamp(self) -> int:
        return self.block["timestamp"]

    def datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.timestamp(), datetime.timezone.utc)

    def is_for_past(self):
        return self.timestamp() < datetime.datetime.now().timestamp() - (60 * 10)

    def __repr__(self):
        return f"{self.w3.provider}, {self.number=}"
