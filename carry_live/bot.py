import logging

from common import util
import numpy as np
from ftx_connector import FtxConnectorRest, FtxConnectorWs
from typing import List, Optional
from types_ import *
import config
from common.logger import logger


def get_funding_rate(symbol: str):
    ts = util.timestamp_now()
    _, fundings = util.get_historical_funding(symbol, ts - 24 * 3600, ts)
    avg = np.mean(fundings)
    return avg * 24 * 365 * 100


class CarryBot:
    def __init__(self):
        self._connector_rest = FtxConnectorRest(config.API_KEY, config.API_SECRET, config.SUB_ACCOUNT)
        self._connector_ws = FtxConnectorWs(config.API_KEY, config.API_SECRET)
        self._connector_ws.receive_tickers_cb = self._receive_tickers
        self._markets_info = self._connector_rest.get_markets_info()
        self._expiry: str = ''
        self._positions = None

    def start(self, coins: List[str], expiry: str) -> None:
        logger.info('CarryBot started')
        self._expiry = expiry
        self._connector_ws.subscribe(coins, expiry)
        self._connector_ws.listen_to_tickers(config.REFRESH_TIME)

    def _receive_tickers(self, tickers: List[TickerCombo]) -> None:
        logger.debug('Process tickers')
        self._update_positions()
        for tickerCombo in tickers:
            self._process_ticker(tickerCombo)

    def _process_ticker(self, tickerCombo: TickerCombo) -> None:
        coin = tickerCombo.coin
        perp_price = tickerCombo.perp_ticker.mark
        fut_price = tickerCombo.fut_ticker.mark
        basis = (perp_price - fut_price) / perp_price * 100

        cache = Cache()
        cache.current_open_threshold = config.INIT_OPEN_THRESHOLD
        cache.read(f'{config.CACHE_FOLDER}/{coin}.json')

        is_trade_on = self._is_trade_on(coin)

        # todo refactor this
        if is_trade_on and abs(basis) < 0.1:
            try:
                self._close_combo_trade(tickerCombo)
                cache.last_open_basis = 0.
                cache.current_open_threshold = config.INIT_OPEN_THRESHOLD
                self._update_positions()
                self._notify(f'Closed trade for {coin}', logging.INFO)
            except Exception as e:
                self._notify(f'Could not close trade for {coin}: {e}', logging.WARNING)

        elif is_trade_on and abs(basis - cache.last_open_basis) > 5:
            try:
                self._close_combo_trade(tickerCombo)
                cache.last_open_basis = 0.
                cache.current_open_threshold = abs(basis) + config.THRESHOLD_INCREMENT
                self._update_positions()
                self._notify(f'Closed trade for {coin}', logging.INFO)
            except Exception as e:
                self._notify(f'Could not close trade for {coin}: {e}', logging.WARNING)

        elif abs(basis) > cache.current_open_threshold:
            try:
                self._open_combo_trade(tickerCombo)
                cache.last_open_basis = abs(basis)
                cache.current_open_threshold = max(basis, cache.current_open_threshold + config.THRESHOLD_INCREMENT)
                self._update_positions()
                self._notify(f'Opened trade for {coin}', logging.INFO)
            except Exception as e:
                self._notify(f'Could not open trade for {coin}: {e}', logging.WARNING)

        # todo refactor this
        perp_pos = self._get_position(util.get_perp_symbol(coin))
        fut_pos = self._get_position(util.get_future_symbol(coin, self._expiry))
        cache.perp_size = None if perp_pos is None else perp_pos.size
        cache.fut_size = None if fut_pos is None else fut_pos.size
        if cache.perp_size is not None or cache.fut_size is not None:
            cache.coin = coin
            cache.perp_price = perp_price
            cache.fut_price = fut_price
            cache.funding = get_funding_rate(util.get_perp_symbol(coin))
            cache.write()
        else:
            # todo delete cache file if exists
            pass

    def _is_trade_on(self, coin: str) -> bool:
        perp_symbol = util.get_perp_symbol(coin)
        fut_symbol = util.get_future_symbol(coin, self._expiry)

        perp_pos = self._get_position(perp_symbol)
        fut_pos = self._get_position(fut_symbol)

        return perp_pos is not None or fut_pos is not None

    def _open_combo_trade(self, tickerCombo: TickerCombo) -> None:
        # todo determine size
        # todo handle strategy
        # buy_id = self.place_order_limit(perp_symbol, 0.8 * perp_price, 0.001, True)
        # if buy_id:
        #     sell_id = self.place_order_limit(fut_symbol, 1.2 * fut_price, 0.001, False)
        #     if not sell_id:
        #         self.cancel_order(buy_id)
        raise Exception(f'open trade not implemented')

    def _close_combo_trade(self, tickerCombo: TickerCombo) -> None:
        raise Exception(f'close trade not implemented')

    def _place_order_limit(self, order: LimitOrder) -> Optional[str]:
        market_info = self._markets_info[order.symbol]
        price_rounded = util.round_to_tick(order.price, market_info.price_increment)
        size_rounded = util.round_to_tick(order.size, market_info.size_increment)
        try:
            if size_rounded < market_info.min_provide_size:
                raise Exception(
                    f'rounded size is {size_rounded}, which is less than the min size {market_info.min_provide_size}')
            if order.is_buy:
                return self._connector_rest.buy_limit(order.symbol, price_rounded, size_rounded)
            else:
                return self._connector_rest.sell_limit(order.symbol, price_rounded, size_rounded)
        except Exception as e:
            logger.error(f'Could not place limit order {order}: {e}')
            return None

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

    def _update_positions(self):
        self._positions = self._get_positions()

    def _notify(self, msg: str, level: int):
        # self.telegram_bot.send(msg, level) todo
        if level == logging.INFO:
            logger.info(msg)
        elif level == logging.WARNING:
            logger.warning(msg)
        elif level == logging.ERROR:
            logger.error(msg)
        else:
            raise Exception(f'Logger level {level} not valid for notification')


if __name__ == '__main__':
    util.create_folder(config.CACHE_FOLDER)
    util.create_folder(config.LOG_FOLDER)
    logger.add_console()
    logger.add_file(config.LOG_FOLDER)

    bot = CarryBot()
    bot.start(config.WHITELIST, '0930')
