from common.FtxClientWs import FtxWebsocketClient
import time
from typing import List
from common import util
from types_ import WsTicker, TickerCombo
from common.util import logger


class FtxConnectorWs:
    def __init__(self, api_key: str = '', api_secret: str = ''):
        self._client = FtxWebsocketClient(api_key, api_secret)
        self._coins: List[str] = []
        self._expiry: str = ''
        self._is_listening: bool = False
        self.process_tickers_cb = None

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
            tickers: List[TickerCombo] = []

            for coin in self._coins:
                perp = util.get_perp_symbol(coin)
                fut = util.get_future_symbol(coin, self._expiry)

                perp_ticker = self._get_ticker(perp)
                fut_ticker = self._get_ticker(fut)

                if perp_ticker is None or fut_ticker is None:
                    continue

                tickers.append(TickerCombo(coin, perp_ticker, fut_ticker))

            self.process_tickers_cb(tickers)
            time.sleep(refresh_time)
