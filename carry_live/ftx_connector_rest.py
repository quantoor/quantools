from common.FtxClientRest import FtxClient
from typing import List, Dict, Optional
from types_ import Position, Order, MarketInfo
from common.util import logger


class FtxConnectorRest:
    def __init__(self, api_key: str = '', api_secret: str = '', subaccount_name: str = ''):
        self._client = FtxClient(api_key, api_secret, subaccount_name)

    def get_markets_info(self) -> Dict[str, MarketInfo]:
        return {market['name']: MarketInfo(market) for market in self._client.get_markets()}

    def buy_limit(self, market: str, price: float, size: float) -> str:
        res = self._client.place_order(market, 'buy', price, size, type='limit', post_only=True)
        if not res:
            raise Exception(f'Result of place order is empty')
        return Order(res).id

    def sell_limit(self, market: str, price: float, size: float) -> str:
        res = self._client.place_order(market, 'sell', price, size, type='limit', post_only=True)
        if not res:
            raise Exception(f'Result of place order is empty')
        return Order(res).id

    def buy_market(self, market: str, size: float):
        res = self._client.place_order(market=market, side='buy', price=0., size=size, type='market')
        if not res:
            raise Exception(f'Result of place order is empty')
        return Order(res)

    def sell_market(self, market: str, size: float):
        res = self._client.place_order(market=market, side='sell', price=0., size=size, type='market')
        if not res:
            raise Exception(f'Result of place order is empty')
        return Order(res)

    def get_positions(self) -> List:
        # filter only positions with size different from 0
        positions = filter(lambda x: x['size'] != 0., self._client.get_positions())
        return [Position(pos) for pos in [*positions]]

    def get_open_orders(self, market: Optional[str] = None) -> List[Order]:
        return [Order(order) for order in self._client.get_open_orders(market)]

    def cancel_orders(self, market: Optional[str] = None) -> None:
        self._client.cancel_orders(market_name=market)

    def cancel_order(self, order_id: str) -> None:
        self._client.cancel_order(order_id)
