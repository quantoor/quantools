from common import util
import numpy as np
from ftx_connector_rest import FtxConnectorRest
from ftx_connector_ws import FtxConnectorWs
from typing import List
from types_ import WsTicker
import config
from common.util import logger


def get_funding_rate(symbol: str):
    ts = util.timestamp_now()
    _, fundings = util.get_historical_funding(symbol, ts - 24 * 3600, ts)
    avg = np.mean(fundings)
    return avg * 24 * 365 * 100


class CarryBot:
    def __init__(self):
        self._connector_rest = FtxConnectorRest(config.API_KEY, config.API_SECRET, config.SUB_ACCOUNT)
        self._connector_ws = FtxConnectorWs(config.API_KEY, config.API_SECRET)
        self._connector_ws.process_ticker_cb = self.process_ticker
        self._expiry: str = ''
        self._markets_info = self._connector_rest.get_markets_info()

    def start(self, coins: List[str], expiry: str):
        self._expiry = expiry
        self._connector_ws.subscribe(coins, expiry)
        self._connector_ws.listen_to_tickers(config.REFRESH_TIME)

    def process_ticker(self, coin: str, perp_ticker: WsTicker, fut_ticker: WsTicker) -> None:
        perp_price = perp_ticker.mark
        fut_price = fut_ticker.mark
        basis = (perp_price - fut_price) / perp_price * 100
        print(f'{coin} basis: {round(basis, 2)}%')

        perp_symbol = util.get_perp_symbol(coin)
        fut_symbol = util.get_future_symbol(coin, self._expiry)

        # todo determine size
        # todo handle strategy
        # buy_id = self.place_order_limit(perp_symbol, 0.8 * perp_price, 0.001, True)
        # if buy_id:
        #     sell_id = self.place_order_limit(fut_symbol, 1.2 * fut_price, 0.001, False)
        #     if not sell_id:
        #         self.cancel_order(buy_id)

    def place_order_limit(self, market: str, price: float, size: float, is_buy: bool) -> str:
        market_info = self._markets_info[market]
        price_rounded = util.round_to_tick(price, market_info.price_increment)
        size_rounded = util.round_to_tick(size, market_info.size_increment)
        if size_rounded < market_info.min_provide_size:
            logger.warn(f'Rounded buy size for {market} is {size_rounded}, which is less than the minimum size')
            return ''
        try:
            if is_buy:
                return self._connector_rest.buy_limit(market, price_rounded, size_rounded)
            else:
                return self._connector_rest.sell_limit(market, price_rounded, size_rounded)
        except Exception as e:
            logger.error(f'Could not place limit {"buy" if is_buy else "sell"} order for {market}: {e}')
            return ''

    def cancel_order(self, order_id: str):
        try:
            self._connector_rest.cancel_order(order_id)
        except Exception as e:
            logger.error(f'Could not cancel order id {order_id}: {e}')


if __name__ == '__main__':
    active_futures = util.get_active_futures_with_expiry()
    _expiry = '0930'
    _coins = [coin for coin in active_futures[_expiry] if coin not in config.BLACKLIST]

    bot = CarryBot()
    bot.start(['BTC'], _expiry)
