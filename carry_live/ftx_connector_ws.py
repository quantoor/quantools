from common.FtxClientWs import FtxWebsocketClient
import time
from typing import List, Dict
from common import util


class FtxConnectorWs:
    def __init__(self):
        self._client = FtxWebsocketClient()
        self._coins: List[str] = []
        self._expiry: str = ''
        self._is_listening = False

    def subscribe(self, coins: List[str], expiry: str) -> None:
        self._coins = coins
        self._expiry = expiry

    def _get_ticker(self, market: str):
        res = self._client.get_ticker(market)
        if len(res) == 0:
            return None
        return WsTicker(res)

    def listen_to_tickers(self, refresh_time: float = 1.) -> None:
        self._is_listening = True

        while self._is_listening:
            for coin in self._coins:
                self._listen_to_ticker(coin)
            time.sleep(refresh_time)

    def _listen_to_ticker(self, coin: str) -> None:
        perp = util.get_perp_symbol(coin)
        fut = util.get_future_symbol(coin, self._expiry)

        perp_ticker = self._get_ticker(perp)
        fut_ticker = self._get_ticker(fut)

        if perp_ticker is None or fut_ticker is None:
            return

        perp_price = perp_ticker.mark
        fut_price = fut_ticker.mark
        basis = (perp_price - fut_price) / perp_price * 100

        print(f'{fut} basis: {round(basis, 2)}%')


class WsTicker:
    def __init__(self, ws_ticker: Dict[str, float]):
        self.bid: float = ws_ticker['bid']
        self.ask: float = ws_ticker['ask']
        self.mark: float = (self.bid + self.ask) / 2
        self.bid_size: float = ws_ticker['bidSize']
        self.ask_size: float = ws_ticker['askSize']
        self.last: float = ws_ticker['last']
        self.time: float = ws_ticker['time']
