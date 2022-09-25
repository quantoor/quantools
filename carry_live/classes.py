from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class WsTicker:
    """Class to parse FTX websocket"""

    def __init__(self, res: Dict[str, float]):
        self.bid: float = res['bid']
        self.ask: float = res['ask']
        self.mark: float = (self.bid + self.ask) / 2
        # self.bid_size: float = res['bidSize']
        # self.ask_size: float = res['askSize']
        self.last: float = res['last']
        # self.time: float = res['time']


class BasisType(Enum):
    CONTANGO = 1
    BACKWARDATION = 2
    UNDEFINED = 3


class TickerCombo:
    def __init__(self, coin: str, expiry: str, perp_ticker: WsTicker, fut_ticker: WsTicker):
        self.coin = coin
        self.expiry = expiry
        self.perp_ticker = perp_ticker
        self.fut_ticker = fut_ticker

        fut_bid, fut_mark, fut_ask = fut_ticker.bid, fut_ticker.mark, fut_ticker.ask
        perp_bid, perp_mark, perp_ask = perp_ticker.bid, perp_ticker.mark, perp_ticker.ask

        self.basis = self._get_basis(perp_mark, fut_mark)

        if perp_bid > fut_ask:
            self.basis_type = BasisType.CONTANGO
        elif fut_bid > perp_ask:
            self.basis_type = BasisType.BACKWARDATION
        else:
            self.basis_type = BasisType.UNDEFINED

    @staticmethod
    def _get_basis(x, y):
        mid = (x + y) / 2
        return (x - y) / mid * 100

    def get_basis_open(self, basis_type: BasisType) -> Optional[float]:
        if basis_type == BasisType.CONTANGO:
            return self._get_basis(self.perp_ticker.bid, self.fut_ticker.ask)
        elif basis_type == BasisType.BACKWARDATION:
            return self._get_basis(self.fut_ticker.bid, self.perp_ticker.ask)
        else:
            return None

    def get_basis_close(self, basis_type: BasisType) -> Optional[float]:
        if basis_type == BasisType.CONTANGO:
            return self._get_basis(self.perp_ticker.ask, self.fut_ticker.bid)
        elif basis_type == BasisType.BACKWARDATION:
            return self._get_basis(self.fut_ticker.ask, self.perp_ticker.bid)
        else:
            return None


class Position:
    """Class to parse FTX websocket"""

    def __init__(self, res: Dict[str, Any]):
        self.symbol: str = res['future']
        self.size: float = res['size']
        self.is_long: bool = res['side'] == 'buy'
        self.entry_price: float = res['entryPrice']
        self.pnl: float = res['recentPnl']


class Order:
    """Class to parse FTX websocket"""

    def __init__(self, res: Dict[str, Any]):
        self.id: str = str(res['id'])
        self.client_id: str = res['clientId']
        self.market: str = res['market']
        self.type: str = res['type']
        self.is_buy: bool = res['side'] == 'buy'
        self.price: float = res['price']
        self.status: str = res['status']
        self.filled_size: float = res['filledSize']
        self.remaining_size: float = res['remainingSize']
        self.created_at: str = res['createdAt']
        # self.future: str = res['future']


class MarketInfo:
    """Class to parse FTX websocket"""

    def __init__(self, res: Dict[str, Any]):
        self.name: str = res['name']
        self.price_increment: float = res['priceIncrement']
        self.size_increment: float = res['sizeIncrement']
        self.min_provide_size: float = res['minProvideSize']
        self.bid: float = res['bid']
        self.ask: float = res['ask']
        self.type: str = res['type']
        self.future_type: str = res['futureType']
        self.underlying: str = res['underlying']


class LimitOrder:
    """Order to be placed"""

    def __init__(self, symbol: str, price: float, size: float, is_buy: bool):
        self.symbol = symbol
        self.price = price
        self.size = size
        self.is_buy = is_buy

    def __str__(self):
        return f'symbol: {self.symbol}, price: {self.price}, size: {self.size}, is_buy: {self.is_buy}'


class StrategyStatus:
    def __init__(self):
        self.coin: str = ''
        self.expiry: str = ''
        self.LOB: float = 0.
        self.perp_size: float = 0.
        self.fut_size: float = 0.
        self.n_positions: int = 0
        self.last_time_udpated: str = ''

    def to_dict(self):
        return {
            "coin": self.coin,
            "expiry": self.expiry,
            "LOB": self.LOB,
            "perp_size": self.perp_size,
            "fut_size": self.fut_size,
            "n_positions": self.n_positions,
            "last_time_updated": self.last_time_udpated
        }

    def from_dict(self, res: dict):
        self.coin = res['coin']
        self.expiry = res['expiry']
        self.LOB = res['LOB']
        self.perp_size = res['perp_size']
        self.fut_size = res['fut_size']
        self.n_positions = res['n_positions']
        self.last_time_udpated = res['last_time_updated']
        return self

    def __str__(self):
        return "{" \
               f"coin: {self.coin}-{self.expiry}," \
               f"LOB: {self.LOB}," \
               f"perp_size: {self.perp_size}," \
               f"fut_size: {self.fut_size}," \
               f"n_positions: {self.n_positions}," \
               f"last_time_updated: {self.last_time_udpated}" \
               "}"


class Trade:
    def __init__(self, res: Dict[str, Any]):
        self.instrument: str = res['future']
        self.trade_id: int = res['tradeId']
        self.order_id: int = res['orderId']
        self.side: str = res['side']
        self.price: float = res['price']
        self.amount: float = res['size']
        self.fee: float = res['fee']
        self.maker: bool = res['liquidity'] == 'maker'
        self.timestamp: int = int(datetime.fromisoformat(res['time']).timestamp() * 1000)
        self.date: str = res['time']
