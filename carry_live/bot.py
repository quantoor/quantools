from common import util
import numpy as np
from ftx_connector_rest import FtxConnectorRest
from ftx_connector_ws import FtxConnectorWs
from typing import List, Optional
from types_ import Position, TickerCombo, Cache
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
        self._positions = None

        util.create_folder(config.CACHE_FOLDER)

    def start(self, coins: List[str], expiry: str) -> None:
        logger.info('Live bot running...')
        self._expiry = expiry
        self._connector_ws.subscribe(coins, expiry)
        self._connector_ws.listen_to_tickers(config.REFRESH_TIME)

    def _process_tickers(self, tickers: List[TickerCombo]) -> None:
        logger.info('Process tickers')
        self._positions = self._get_positions()
        for tickerCombo in tickers:
            self._process_ticker(tickerCombo)

    def _process_ticker(self, tickerCombo: TickerCombo) -> None:
        coin = tickerCombo.coin
        perp_price = tickerCombo.perp_ticker.mark
        fut_price = tickerCombo.fut_ticker.mark
        basis = (perp_price - fut_price) / perp_price * 100

        cache = Cache(f'{config.CACHE_FOLDER}/{coin}.json')

        is_trade_on = self._is_trade_on(coin)
        if is_trade_on and abs(basis) < 0.1:
            if self._close_trade(tickerCombo):
                self._positions = self._get_positions()
                logger.info('')
            else:
                logger.warning('')

        elif is_trade_on and abs(basis - cache.last_open_basis) > 5:
            if self._close_trade(tickerCombo):
                cache.last_open_basis = 0.
                cache.current_open_threshold = abs(basis)
                self._positions = self._get_positions()
                logger.info('')
            else:
                logger.warning('')

        elif abs(basis) > cache.current_open_threshold:
            if self._open_trade(tickerCombo):
                cache.last_open_basis = abs(basis)
                cache.current_open_threshold = max(basis, cache.current_open_threshold + 1)
                self._positions = self._get_positions()
                logger.info('')
            else:
                logger.warning('')

        # todo refactor this
        cache.coin = coin
        cache.perp_price = perp_price
        perp_pos = self._get_position(util.get_perp_symbol(coin))
        cache.perp_size = None if perp_pos is None else perp_pos.size
        cache.fut_price = fut_price
        fut_pos = self._get_position(util.get_future_symbol(coin, self._expiry))
        cache.fut_size = None if fut_pos is None else fut_pos.size
        cache.write()

    def _is_trade_on(self, coin: str) -> bool:
        perp_symbol = util.get_perp_symbol(coin)
        fut_symbol = util.get_future_symbol(coin, self._expiry)

        perp_pos = self._get_position(perp_symbol)
        fut_pos = self._get_position(fut_symbol)

        return perp_pos is not None or fut_pos is not None

    def _open_trade(self, tickerCombo: TickerCombo) -> bool:
        # todo determine size
        # todo handle strategy
        # buy_id = self.place_order_limit(perp_symbol, 0.8 * perp_price, 0.001, True)
        # if buy_id:
        #     sell_id = self.place_order_limit(fut_symbol, 1.2 * fut_price, 0.001, False)
        #     if not sell_id:
        #         self.cancel_order(buy_id)
        pass

    def _close_trade(self, tickerCombo: TickerCombo) -> bool:
        pass

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

    def _cancel_orders(self) -> None:
        self._connector_rest.cancel_orders()

    def _cancel_order(self, order_id: str) -> None:
        try:
            self._connector_rest.cancel_order(order_id)
        except Exception as e:
            logger.error(f'Could not cancel order id {order_id}: {e}')

    def _get_positions(self) -> List[Position]:
        return self._connector_rest.get_positions()

    def _get_position(self, symbol: str) -> Optional[Position]:
        position = [*filter(lambda x: x.symbol == symbol, self._positions)]
        if len(position) == 0:
            return None
        return position[0]


if __name__ == '__main__':
    active_futures = util.get_active_futures_with_expiry()
    _expiry = '0930'
    _coins = [coin for coin in active_futures[_expiry] if coin not in config.BLACKLIST]

    bot = CarryBot()
    bot.start(_coins, _expiry)
