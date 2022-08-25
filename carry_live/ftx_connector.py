from common.FtxClientRest import FtxClient
from common.FtxClientWs import FtxWebsocketClient
from classes import *
from common import util
from typing import List, Dict, Optional
import time


class FtxConnectorRest:
    def __init__(self, api_key: str = '', api_secret: str = '', subaccount_name: str = ''):
        self._client = FtxClient(api_key, api_secret, subaccount_name)

    def get_markets_info(self) -> Dict[str, MarketInfo]:
        return {market['name']: MarketInfo(market) for market in self._client.get_markets()}

    def buy_limit(self, market: str, price: float, size: float) -> str:
        res = self._client.place_order(market, 'buy', price, size, type='limit', post_only=False)
        if not res:
            raise Exception(f'Result of place order is empty')
        return Order(res).id

    def sell_limit(self, market: str, price: float, size: float) -> str:
        res = self._client.place_order(market, 'sell', price, size, type='limit', post_only=False)
        if not res:
            raise Exception(f'Result of place order is empty')
        return Order(res).id

    def buy_market(self, market: str, size: float) -> str:
        res = self._client.place_order(market=market, side='buy', price=0., size=size, type='market')
        if not res:
            raise Exception(f'Result of place order is empty')
        return Order(res).id

    def sell_market(self, market: str, size: float) -> str:
        res = self._client.place_order(market=market, side='sell', price=0., size=size, type='market')
        if not res:
            raise Exception(f'Result of place order is empty')
        return Order(res).id

    def get_positions(self) -> List[Position]:
        # return only positions with size different from 0
        positions = filter(lambda x: x['size'] != 0., self._client.get_positions())
        return [Position(pos) for pos in [*positions]]

    def get_open_orders(self, market: Optional[str] = None) -> List[Order]:
        return [Order(order) for order in self._client.get_open_orders(market)]

    def cancel_orders(self, market: Optional[str] = None) -> None:
        self._client.cancel_orders(market_name=market)

    def cancel_order(self, order_id: str) -> None:
        res = self._client.cancel_order(order_id)
        if res != "Order queued for cancellation":
            raise Exception(res)


class FtxConnectorWs:
    def __init__(self, api_key: str = '', api_secret: str = ''):
        self._client = FtxWebsocketClient(api_key, api_secret)
        self._coins: List[str] = []
        self._expiry: str = ''
        self._is_listening: bool = False
        self.receive_tickers_cb = None

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

            self.receive_tickers_cb(tickers)
            time.sleep(refresh_time)
