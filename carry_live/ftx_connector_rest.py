from common.FtxClientRest import FtxClient
from typing import List, Dict, Optional
from types_ import Position, OpenOrder
from common.util import logger


class FtxConnectorRest:
    def __init__(self, api_key: str = '', api_secret: str = '', subaccount_name: str = ''):
        self._client = FtxClient(api_key, api_secret, subaccount_name)

    def buy_limit(self, market: str, price: float, size: float):
        return self._client.place_order(market, 'buy', price, size, type='limit', post_only=True)

    def sell_limit(self, market: str, price: float, size: float):
        return self._client.place_order(market, 'sell', price, size, type='limit', post_only=True)

    def buy_market(self, market: str, size: float):
        return self._client.place_order(market=market, side='buy', price=0., size=size, type='market')

    def sell_market(self, market: str, size: float):
        return self._client.place_order(market=market, side='sell', price=0., size=size, type='market')

    def get_positions(self) -> List:
        # filter only positions with size different from 0
        positions = filter(lambda x: x['size'] != 0., self._client.get_positions())
        return [Position(pos) for pos in [*positions]]

    def get_open_orders(self, market: Optional[str] = None) -> List[OpenOrder]:
        return [OpenOrder(order) for order in self._client.get_open_orders(market)]

    def cancel_orders(self, market: Optional[str] = None) -> bool:
        try:
            self._client.cancel_orders(market_name=market)
        except Exception as e:
            logger.error(f'Could not cancel orders: {e}')
            return False
        return True

    def cancel_order(self, order_id: str) -> bool:
        try:
            self._client.cancel_order(order_id)
        except Exception as e:
            logger.error(f'Could not cancel order id {order_id}: {e}')
            return False
        return True
