import importer
from common import util
import numpy as np
from ftx_connector import FtxConnectorRest, FtxConnectorWs
from typing import List, Optional
from types_ import *
import config as cfg
import logging
from common.logger import logger
from telegram_bot import *


class CarryBot:
    def __init__(self):
        self._connector_rest = FtxConnectorRest(cfg.API_KEY, cfg.API_SECRET, cfg.SUB_ACCOUNT)
        self._connector_ws = FtxConnectorWs(cfg.API_KEY, cfg.API_SECRET)
        self._connector_ws.receive_tickers_cb = self._receive_tickers
        self._markets_info = self._connector_rest.get_markets_info()
        self._expiry: str = ''
        self._positions = None

    def start(self, coins: List[str], expiry: str) -> None:
        logger.info('CarryBot started')
        self._expiry = expiry
        self._connector_ws.subscribe(coins, expiry)
        self._connector_ws.listen_to_tickers(cfg.REFRESH_TIME)

    def _receive_tickers(self, tickers: List[TickerCombo]) -> None:
        logger.debug('Process tickers')
        self._update_positions()
        for tickerCombo in tickers:
            self._process_ticker(tickerCombo)

    def _process_ticker(self, tickerCombo: TickerCombo) -> None:
        coin = tickerCombo.coin
        basis = tickerCombo.basis
        adj_basis_open = tickerCombo.adj_basis_open
        adj_basis_close = tickerCombo.adj_basis_close

        # todo refactor this
        self.cache = Cache()
        self.cache.current_open_threshold = cfg.INIT_OPEN_THRESHOLD
        self.cache.read(f'{cfg.CACHE_FOLDER}/{coin}.json')

        is_trade_on = self._is_trade_on(coin)
        if is_trade_on and abs(adj_basis_close) < 0.1:  # todo remove hardcoding
            if cfg.LIVE_TRADE:
                try:
                    if self._close_position(tickerCombo):
                        self._notify(TgMsg(coin, TG_ALWAYS_NOTIFY, f'Closed trade for {coin}'), logging.INFO)
                except Exception as e:
                    self._notify(TgMsg(coin, TG_ERROR, f'Could not close trade for {coin}: {e}'), logging.ERROR)
            else:
                self._notify(
                    TgMsg(coin,
                          TG_CAN_CLOSE,
                          f'{coin} basis is {round(basis, 2)} ({round(adj_basis_close, 2)}) and could close a trade'),
                    logging.INFO)

        elif is_trade_on and abs(abs(adj_basis_close) - self.cache.last_open_basis) > 5:  # todo remove hardcoding
            self._notify(
                TgMsg(coin,
                      TG_CAN_CLOSE,
                      f'{coin} basis is {round(basis, 2)} ({round(adj_basis_close, 2)}) and has decreased more than 5 points'),
                logging.INFO)

        elif abs(adj_basis_open) > self.cache.current_open_threshold:
            if cfg.LIVE_TRADE:
                try:
                    if self._open_position(tickerCombo):
                        self._notify(TgMsg(coin, TG_ALWAYS_NOTIFY, f'Opened trade for {coin}'), logging.INFO)
                except Exception as e:
                    self._notify(TgMsg(coin, TG_ERROR, f'Could not open trade for {coin}: {e}'), logging.ERROR)
            else:
                self._notify(
                    TgMsg(coin,
                          TG_CAN_OPEN,
                          f'{coin} basis is {round(basis, 2)} ({round(adj_basis_open, 2)}) and could open a trade'),
                    logging.INFO)

        # todo refactor this
        perp_pos = self._get_position(util.get_perp_symbol(coin))
        fut_pos = self._get_position(util.get_future_symbol(coin, self._expiry))
        self.cache.perp_size = None if perp_pos is None else perp_pos.size
        self.cache.fut_size = None if fut_pos is None else fut_pos.size
        if self.cache.perp_size is not None or self.cache.fut_size is not None:
            self.cache.coin = coin
            self.cache.basis = basis
            self.cache.adj_basis_open = adj_basis_open
            self.cache.adj_basis_close = adj_basis_close
            self.cache.funding = util.get_funding_rate_avg_24h(util.get_perp_symbol(coin))
            self.cache.write()
        # else:
        #     # delete cache file if exists
        #     if util.file_exists(self.cache.path):
        #         if not util.delete_file(self.cache.path):
        #             logger.warning(f'Could not delete cache file {self.cache.path}')

    def _is_trade_on(self, coin: str) -> bool:
        perp_symbol = util.get_perp_symbol(coin)
        fut_symbol = util.get_future_symbol(coin, self._expiry)

        perp_pos = self._get_position(perp_symbol)
        fut_pos = self._get_position(fut_symbol)

        return perp_pos is not None or fut_pos is not None

    def _open_position(self, tickerCombo: TickerCombo) -> bool:
        perp_symbol = util.get_perp_symbol(tickerCombo.coin)
        fut_symbol = util.get_future_symbol(tickerCombo.coin, self._expiry)

        perp_ticker = tickerCombo.perp_ticker
        fut_ticker = tickerCombo.fut_ticker

        # check if there are already open orders
        open_orders = self._connector_rest.get_open_orders()
        for order in open_orders:
            if order.market in [perp_symbol, fut_symbol]:
                return False

        offset = 1.2

        if tickerCombo.is_contango:
            # sell perp, buy future
            size = cfg.TRADE_SIZE_USD / perp_ticker.mark
            ask_order = LimitOrder(symbol=perp_symbol, price=perp_ticker.bid * offset, size=size, is_buy=False)
            bid_order = LimitOrder(symbol=fut_symbol, price=fut_ticker.ask / offset, size=size, is_buy=True)
        else:
            # sell future, buy perp
            size = cfg.TRADE_SIZE_USD / fut_ticker.mark
            ask_order = LimitOrder(symbol=fut_symbol, price=fut_ticker.bid * offset, size=size, is_buy=False)
            bid_order = LimitOrder(symbol=perp_symbol, price=perp_ticker.ask / offset, size=size, is_buy=True)

        order_id = self._place_order_limit(bid_order)
        try:
            self._place_order_limit(ask_order)
        except Exception as e:
            self._connector_rest.cancel_order(order_id)
            raise Exception(str(e))

        adj_basis_open = tickerCombo.adj_basis_open
        self.cache.last_open_basis = abs(adj_basis_open)
        self.cache.current_open_threshold = max(adj_basis_open,
                                                self.cache.current_open_threshold + cfg.THRESHOLD_INCREMENT)
        self._update_positions()
        return True

    def _close_position(self, tickerCombo: TickerCombo) -> bool:
        perp_symbol = util.get_perp_symbol(tickerCombo.coin)
        fut_symbol = util.get_future_symbol(tickerCombo.coin, self._expiry)

        perp_ticker = tickerCombo.perp_ticker
        fut_ticker = tickerCombo.fut_ticker

        # check if there are already open orders
        open_orders = self._connector_rest.get_open_orders()
        for order in open_orders:
            if order.market in [perp_symbol, fut_symbol]:
                return False

        offset = 1.2

        perp_pos = self._get_position(perp_symbol)
        if perp_pos.is_long:
            # sell perp, buy future
            size = perp_ticker.mark / cfg.TRADE_SIZE_USD
            ask_order = LimitOrder(symbol=perp_symbol, price=perp_ticker.bid * offset, size=size, is_buy=False)
            bid_order = LimitOrder(symbol=fut_symbol, price=fut_ticker.ask / offset, size=size, is_buy=True)
        else:
            # sell future, buy perp
            size = fut_ticker.mark / cfg.TRADE_SIZE_USD
            ask_order = LimitOrder(symbol=fut_symbol, price=fut_ticker.bid * offset, size=size, is_buy=False)
            bid_order = LimitOrder(symbol=perp_symbol, price=perp_ticker.ask / offset, size=size, is_buy=True)

        order_id = self._place_order_limit(bid_order)
        try:
            self._place_order_limit(ask_order)
        except Exception as e:
            self._connector_rest.cancel_order(order_id)
            raise Exception(str(e))

        self.cache.last_open_basis = 0
        self.cache.current_open_threshold = cfg.INIT_OPEN_THRESHOLD
        self._update_positions()
        return True

    def _place_order_limit(self, order: LimitOrder) -> str:
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
            raise Exception(f'could not place limit order {order}: {e}')

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

    @staticmethod
    def _notify(tg_msg: TgMsg, level: int):
        tg_bot.send(tg_msg, level)
        if level == logging.INFO:
            logger.info(tg_msg.msg)
        elif level == logging.WARNING:
            logger.warning(tg_msg.msg)
        elif level == logging.ERROR:
            logger.error(tg_msg.msg)
        else:
            raise Exception(f'Logger level {level} not valid for notification')


if __name__ == '__main__':
    util.create_folder(cfg.CACHE_FOLDER)
    util.create_folder(cfg.LOG_FOLDER)
    logger.add_console()
    logger.add_file(cfg.LOG_FOLDER)
    bot = CarryBot()
    bot.start(cfg.WHITELIST, '0930')
