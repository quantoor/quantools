from common import util
import numpy as np
from ftx_connector_rest import FtxConnectorRest
from ftx_connector_ws import FtxConnectorWs
from typing import List
from types_ import WsTicker, TickerCombo
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
        self._connector_ws.process_tickers_cb = self._process_tickers
        self._expiry: str = ''
        self._markets_info = self._connector_rest.get_markets_info()
        self.positions = None

        util.create_folder(config.CACHE_FOLDER)

    def start(self, coins: List[str], expiry: str):
        self._expiry = expiry
        self._connector_ws.subscribe(coins, expiry)
        self._connector_ws.listen_to_tickers(config.REFRESH_TIME)

    def _process_tickers(self, tickers: List[TickerCombo]):
        self.positions = self._get_positions()
        for tickerCombo in tickers:
            self._process_ticker(tickerCombo)

    def _process_ticker(self, tickerCombo: TickerCombo) -> None:
        coin = tickerCombo.coin
        perp_price = tickerCombo.perp_ticker.mark
        fut_price = tickerCombo.fut_ticker.mark
        basis = (perp_price - fut_price) / perp_price * 100

        if abs(basis) > 1:
            print(f'{coin} basis: {round(basis, 2)}%')

        perp_symbol = util.get_perp_symbol(coin)
        fut_symbol = util.get_future_symbol(coin, self._expiry)

        perp_pos = self._get_position(perp_symbol)
        fut_pos = self._get_position(fut_symbol)

        if perp_pos is not None:
            pass

        # todo determine size
        # todo handle strategy
        # buy_id = self.place_order_limit(perp_symbol, 0.8 * perp_price, 0.001, True)
        # if buy_id:
        #     sell_id = self.place_order_limit(fut_symbol, 1.2 * fut_price, 0.001, False)
        #     if not sell_id:
        #         self.cancel_order(buy_id)

    def _place_order_limit(self, market: str, price: float, size: float, is_buy: bool) -> str:
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

    def _cancel_order(self, order_id: str):
        try:
            self._connector_rest.cancel_order(order_id)
        except Exception as e:
            logger.error(f'Could not cancel order id {order_id}: {e}')

    def _get_positions(self):
        return self._connector_rest.get_positions()

    def _get_position(self, symbol: str):
        position = [*filter(lambda x: x.symbol == symbol, self.positions)]
        if len(position) == 0:
            return None
        return position[0]


if __name__ == '__main__':
    active_futures = util.get_active_futures_with_expiry()
    _expiry = '0930'
    _coins = [coin for coin in active_futures[_expiry] if coin not in config.BLACKLIST]

    bot = CarryBot()
    bot.start(_coins, _expiry)
