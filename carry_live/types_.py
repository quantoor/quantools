from typing import Dict, Any
import json
from common import util


class WsTicker:
    def __init__(self, res: Dict[str, float]):
        self.bid: float = res['bid']
        self.ask: float = res['ask']
        self.mark: float = (self.bid + self.ask) / 2
        self.bid_size: float = res['bidSize']
        self.ask_size: float = res['askSize']
        self.last: float = res['last']
        self.time: float = res['time']


class TickerCombo:
    def __init__(self, coin: str, perp_ticker: WsTicker, fut_ticker: WsTicker):
        self.coin = coin
        self.perp_ticker = perp_ticker
        self.fut_ticker = fut_ticker


class Position:
    def __init__(self, res: Dict[str, Any]):
        self.symbol: str = res['future']
        self.size: float = res['size']
        self.side: bool = res['side']
        # todo


class Order:
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
        self.future: str = res['future']


class MarketInfo:
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


class Cache:
    def __init__(self, path: str):
        self._path: str = path
        self.last_open_basis: float = 0.
        self.current_open_threshold: float = 0.

        if util.file_exists(path):
            with open(self._path, 'r') as f:
                data = json.load(f)
                self.last_open_basis = data['last_open_basis']
                self.current_open_threshold = data['current_open_threshold']

    def write(self):
        with open(self._path, 'w') as f:
            f.write(json.dumps(
                {"last_open_basis": self.last_open_basis, "current_open_threshold": self.current_open_threshold}))
