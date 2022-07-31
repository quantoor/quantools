from common.FtxClientWs import FtxWebsocketClient
import time


class WsTicker:
    def __init__(self):
        self.bid: float
        self.ask: float
        self.bid_size: float
        self.ask_size: float
        self.last: float
        self.time: float


class FtxConnectorWs:
    def __init__(self):
        self.client = FtxWebsocketClient()

    def start(self):
        for i in range(1000):
            print(self.client.get_ticker('BTC-0930'))
            time.sleep(0.01)
