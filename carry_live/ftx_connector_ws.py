from common.FtxClientWs import FtxWebsocketClient
import time
from typing import List
from common import util
from types_ import WsTicker


class FtxConnectorWs:
    def __init__(self):
        self._client = FtxWebsocketClient()
        self._coins: List[str] = []
        self._expiry: str = ''
        self._is_listening: bool = False
        self.process_ticker_cb = None

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

        self.process_ticker_cb(fut, perp_ticker, fut_ticker)
