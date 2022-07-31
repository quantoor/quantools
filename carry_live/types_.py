from typing import Dict


class WsTicker:
    def __init__(self, ws_ticker: Dict[str, float]):
        self.bid: float = ws_ticker['bid']
        self.ask: float = ws_ticker['ask']
        self.mark: float = (self.bid + self.ask) / 2
        self.bid_size: float = ws_ticker['bidSize']
        self.ask_size: float = ws_ticker['askSize']
        self.last: float = ws_ticker['last']
        self.time: float = ws_ticker['time']
