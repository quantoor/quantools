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


class OpenOrder:
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
