from common.FtxClientRest import FtxClient
import time
from typing import List, Dict
from common import util


class FtxConnectorRest:
    def __init__(self):
        self._client = FtxClient()

    def buy_limit(self, market: str, price: float, size: float):
        self._client.place_order(market, 'buy', price, size, type='limit')

    def sell_limit(self, market: str, price: float, size: float):
        self._client.place_order(market, 'sell', price, size, type='limit')

    def buy_market(self, market: str, size: float):
        self._client.place_order(market=market, side='buy', price=0., size=size, type='market')

    def sell_market(self, market: str, size: float):
        self._client.place_order(market=market, side='sell', price=0., size=size, type='market')
