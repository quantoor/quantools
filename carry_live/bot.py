from ftx_connector import FtxConnectorRest, FtxConnectorWs
from typing import List, Optional, Tuple
from classes import *
from common.logger import logger
from telegram_bot import *
import config as cfg
import logging
from redis_client import RedisClient


def _notify(tg_msg: TgMsg):
    tg_bot.send(tg_msg)
    level = tg_msg.level
    msg = tg_msg.msg
    if level == logging.INFO:
        logger.info(msg)
    elif level == logging.WARNING:
        logger.warning(msg)
    elif level == logging.ERROR:
        logger.error(msg)
    else:
        logger.error(f'Logger level {level} not valid for notification. {msg}')


class CarryBot:
    def __init__(self):
        self._connector_ws = FtxConnectorWs(cfg.API_KEY, cfg.API_SECRET)
        self._connector_ws.receive_tickers_cb = self._receive_tickers
        self._strategy_manager = StrategyManager()

    def start(self, coins: List[str], expiry: str) -> None:
        self._connector_ws.subscribe(coins, expiry)
        self._connector_ws.listen_to_tickers(cfg.REFRESH_TIME)

    def _receive_tickers(self, tickers: List[TickerCombo]) -> None:
        logger.debug('Receive tickers')
        self._strategy_manager.update_positions()
        for ticker_combo in tickers:
            self._strategy_manager.process_ticker(ticker_combo)


class StrategyManager:
    def __init__(self):
        self._offset = cfg.SPREAD_OFFSET
        self._positions = None
        self._strategy_status = None
        self._rest_manager = RestManager()
        self._r = RedisClient()

    def process_ticker(self, ticker_combo: TickerCombo) -> None:
        coin = ticker_combo.coin
        expiry = ticker_combo.expiry

        # load strategy status
        self._strategy_status = self._r.get(coin)
        if self._strategy_status is None:
            self._strategy_status = StrategyStatus()

        # check current position
        is_position_open, basis_type = self._is_position_open(coin, expiry)
        if is_position_open:
            if basis_type == BasisType.UNDEFINED:
                logger.error(f'Basis for open position for {coin} is not defined')
                return
            self._handle_open_position(ticker_combo)
        else:
            if basis_type == BasisType.UNDEFINED:
                return
            self._handle_no_position(ticker_combo)

        perp_pos = self._get_position(util.get_perp_symbol(coin))
        fut_pos = self._get_position(util.get_future_symbol(coin, expiry))

        self._strategy_status.perp_size = None if perp_pos is None else perp_pos.size
        self._strategy_status.fut_size = None if fut_pos is None else fut_pos.size

        if self._strategy_status.perp_size is not None or self._strategy_status.fut_size is not None:
            self._strategy_status.coin = coin
            self._strategy_status.basis = ticker_combo.basis

    def _handle_open_position(self, ticker_combo: TickerCombo):
        coin = ticker_combo.coin
        basis_close = ticker_combo.get_basis_close(ticker_combo.basis_type)
        basis_open = ticker_combo.get_basis_open(ticker_combo.basis_type)

        if abs(basis_close) < 0.1:
            if cfg.LIVE_TRADE:
                try:
                    self._close_position(ticker_combo)
                except Exception as e:
                    msg = f'Could not close position for {coin}: {e}'
                    _notify(TgMsg(coin, TG_ERROR, msg, logging.ERROR))
            else:
                msg = f'{coin} basis is {round(basis_close, 2)} and could close position'
                _notify(TgMsg(coin, TG_CAN_CLOSE, msg, logging.INFO))

        elif abs(basis_open) > self._strategy_status.last_open_basis + cfg.THRESHOLD_INCREMENT:
            pass  # todo check risk limit

            if cfg.LIVE_TRADE:
                try:
                    self._open_position(ticker_combo)
                except Exception as e:
                    msg = f'Could not open trade for {coin}: {e}'
                    _notify(TgMsg(coin, TG_ERROR, msg, logging.ERROR))
            else:
                msg = f'{coin} basis is {round(basis_close, 2)} and could increment position'
                _notify(TgMsg(coin, TG_CAN_CLOSE, msg, logging.INFO))

    def _handle_no_position(self, ticker_combo: TickerCombo):
        coin = ticker_combo.coin
        basis_open = ticker_combo.get_basis_open(ticker_combo.basis_type)
        if abs(basis_open) > cfg.THRESHOLD_INCREMENT:
            if cfg.LIVE_TRADE:
                try:
                    self._open_position(ticker_combo)
                except Exception as e:
                    msg = f'Could not open position for {coin}: {e}'
                    _notify(TgMsg(coin, TG_ERROR, msg, logging.ERROR))
            else:
                msg = f'{coin} basis is {round(basis_open, 2)} and could open position'
                _notify(TgMsg(coin, TG_CAN_OPEN, msg, logging.INFO))

    def _is_position_open(self, coin: str, expiry: str) -> Tuple[bool, BasisType]:
        perp_pos = self._get_position(util.get_perp_symbol(coin))
        fut_pos = self._get_position(util.get_future_symbol(coin, expiry))

        if perp_pos is None or fut_pos is None:
            return False, BasisType.UNDEFINED

        if not perp_pos.is_long and fut_pos.is_long:
            return True, BasisType.CONTANGO
        elif perp_pos.is_long and not fut_pos.is_long:
            return True, BasisType.BACKWARDATION
        else:
            return True, BasisType.UNDEFINED

    def _open_position(self, ticker_combo: TickerCombo) -> None:
        perp_symbol = util.get_perp_symbol(ticker_combo.coin)
        fut_symbol = util.get_future_symbol(ticker_combo.coin, ticker_combo.expiry)

        perp_ticker = ticker_combo.perp_ticker
        fut_ticker = ticker_combo.fut_ticker

        # check if there are already open orders
        open_orders = self._rest_manager.get_open_orders()
        for order in open_orders:
            if order.market in [perp_symbol, fut_symbol]:
                return

        size = cfg.TRADE_SIZE_USD / max(perp_ticker.mark, fut_ticker.mark)

        if ticker_combo.basis_type == BasisType.CONTANGO:
            # sell perp, buy future
            ask_order = LimitOrder(symbol=perp_symbol, price=perp_ticker.bid * self._offset, size=size, is_buy=False)
            bid_order = LimitOrder(symbol=fut_symbol, price=fut_ticker.ask / self._offset, size=size, is_buy=True)
        else:
            # sell future, buy perp
            ask_order = LimitOrder(symbol=fut_symbol, price=fut_ticker.bid * self._offset, size=size, is_buy=False)
            bid_order = LimitOrder(symbol=perp_symbol, price=perp_ticker.ask / self._offset, size=size, is_buy=True)

        order_id = self._rest_manager.place_order_limit(bid_order)
        try:
            self._rest_manager.place_order_limit(ask_order)
        except Exception as e:
            self._rest_manager.cancel_order(order_id)
            raise Exception(str(e))

        adj_basis_open = ticker_combo.get_basis_open(ticker_combo.basis_type)
        self._strategy_status.last_open_basis = abs(adj_basis_open)
        self.update_positions()
        msg = f'Opened position for {ticker_combo.coin}'
        _notify(TgMsg(ticker_combo.coin, TG_ALWAYS_NOTIFY, msg, logging.INFO))

    def _close_position(self, ticker_combo: TickerCombo) -> None:
        perp_symbol = util.get_perp_symbol(ticker_combo.coin)
        fut_symbol = util.get_future_symbol(ticker_combo.coin, ticker_combo.expiry)

        perp_ticker = ticker_combo.perp_ticker
        fut_ticker = ticker_combo.fut_ticker

        # check if there are already open orders
        open_orders = self._rest_manager.get_open_orders()
        for order in open_orders:
            if order.market in [perp_symbol, fut_symbol]:
                return

        perp_pos = self._get_position(perp_symbol)
        if perp_pos.is_long:
            # sell perp, buy future
            size = perp_ticker.mark / cfg.TRADE_SIZE_USD
            ask_order = LimitOrder(symbol=perp_symbol, price=perp_ticker.bid * self._offset, size=size, is_buy=False)
            bid_order = LimitOrder(symbol=fut_symbol, price=fut_ticker.ask / self._offset, size=size, is_buy=True)
        else:
            # sell future, buy perp
            size = fut_ticker.mark / cfg.TRADE_SIZE_USD
            ask_order = LimitOrder(symbol=fut_symbol, price=fut_ticker.bid * self._offset, size=size, is_buy=False)
            bid_order = LimitOrder(symbol=perp_symbol, price=perp_ticker.ask / self._offset, size=size, is_buy=True)

        order_id = self._rest_manager.place_order_limit(bid_order)
        try:
            self._rest_manager.place_order_limit(ask_order)
        except Exception as e:
            self._rest_manager.cancel_order(order_id)
            raise Exception(str(e))

        self._strategy_status.last_open_basis = 0
        self.update_positions()
        msg = f'Closed position for {ticker_combo.coin}'
        _notify(TgMsg(ticker_combo.coin, TG_ALWAYS_NOTIFY, msg, logging.INFO))

    def _get_position(self, symbol: str) -> Optional[Position]:
        position = [*filter(lambda x: x.symbol == symbol, self._positions)]
        if len(position) == 0:
            return None
        return position[0]

    def update_positions(self):
        self._positions = self._rest_manager.get_positions()


class RestManager:
    def __init__(self):
        self._connector_rest = FtxConnectorRest(cfg.API_KEY, cfg.API_SECRET, cfg.SUB_ACCOUNT)
        self._markets_info = self._connector_rest.get_markets_info()

    def place_order_limit(self, order: LimitOrder) -> str:
        market_info = self._markets_info[order.symbol]
        price_rounded = util.round_to_tick(order.price, market_info.price_increment)
        size_rounded = util.round_to_tick(order.size, market_info.size_increment)
        try:
            if size_rounded < market_info.min_provide_size:
                raise Exception(
                    f'rounded size is {size_rounded}, which is less than the min size {market_info.min_provide_size}')

            return self._connector_rest.place_order_limit(order.symbol, order.is_buy, price_rounded, size_rounded)

        except Exception as e:
            raise Exception(f'could not place limit order {order}: {e}')

    def get_open_orders(self) -> List[Order]:
        return self._connector_rest.get_open_orders()

    def cancel_orders(self) -> None:
        self._connector_rest.cancel_orders()

    def cancel_order(self, order_id: str) -> None:
        try:
            self._connector_rest.cancel_order(order_id)
        except Exception as e:
            logger.error(f'Could not cancel order id {order_id}: {e}')

    def get_positions(self) -> List[Position]:
        return self._connector_rest.get_positions()
