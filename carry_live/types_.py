from typing import Dict, Any
import json
from common import util
from common.logger import logger


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
        self.coin: str = ''
        self.last_open_basis: float = 0.
        self.current_open_threshold: float = 0.
        self.perp_price: float = 0.
        self.perp_size: float = 0.
        self.fut_price: float = 0.
        self.fut_size: float = 0.
        self.funding: float = 0.

        if util.file_exists(path):
            try:
                with open(self._path, 'r') as f:
                    data = json.load(f)
                    self.coin = data['coin']
                    self.last_open_basis = data['last_open_basis']
                    self.current_open_threshold = data['current_open_threshold']
                    self.perp_price = data['perp_price']
                    self.perp_size = data['perp_size']
                    self.fut_price = data['fut_price']
                    self.fut_size = data['fut_size']
                    self.funding = data['funding']
            except Exception as e:
                logger.error(f'Error reading cache at path {path}: {e}')

    def write(self):
        with open(self._path, 'w') as f:
            f.write(json.dumps(self.get_dict()))

    def get_dict(self):
        return {
            "coin": self.coin,
            "last_open_basis": self.last_open_basis,
            "current_open_threshold": self.current_open_threshold,
            "perp_price": self.perp_price,
            "perp_size": self.perp_size,
            "fut_price": self.fut_price,
            "fut_size": self.fut_size,
            "funding": self.funding
        }
