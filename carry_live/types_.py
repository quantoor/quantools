from typing import Dict, Any


class WsTicker:
    def __init__(self, res: Dict[str, float]):
        self.bid: float = res['bid']
        self.ask: float = res['ask']
        self.mark: float = (self.bid + self.ask) / 2
        self.bid_size: float = res['bidSize']
        self.ask_size: float = res['askSize']
        self.last: float = res['last']
        self.time: float = res['time']


class Position:
    def __init__(self, res: Dict[str, Any]):
        self.future: str = res['future']
        self.size: float = res['size']
        self.side: bool = res['side']
        self.net_size: float = res['netSize']
        # todo


class Order:
    def __init__(self, res: Dict[str, Any]):
        self.id: int = res['id']
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
        self.size_increment: str = res['sizeIncrement']
        self.min_provide_size: str = res['minProvideSize']
        self.bid: float = res['bid']
        self.ask: float = res['ask']
        self.type: str = res['type']
        self.future_type: str = res['futureType']
        self.underlying: str = res['underlying']
