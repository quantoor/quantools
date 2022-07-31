from common.FtxClientRest import FtxClient
import time
from typing import List, Dict
from common import util


class FtxConnectorRest:
    def __init__(self, api_key: str = '', api_secret: str = '', subaccount_name: str = ''):
        self._client = FtxClient(api_key, api_secret, subaccount_name)

    def buy_limit(self, market: str, price: float, size: float):
        self._client.place_order(market, 'buy', price, size, type='limit')

    def sell_limit(self, market: str, price: float, size: float):
        self._client.place_order(market, 'sell', price, size, type='limit')

    def buy_market(self, market: str, size: float):
        self._client.place_order(market=market, side='buy', price=0., size=size, type='market')

    def sell_market(self, market: str, size: float):
        self._client.place_order(market=market, side='sell', price=0., size=size, type='market')

    def get_positions(self):
        # filter only positions with size different from 0
        positions = filter(lambda x: x['size'] != 0., self._client.get_positions())
        return [*positions]
