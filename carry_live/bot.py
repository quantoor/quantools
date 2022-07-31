from common import util
import numpy as np
from ftx_connector_rest import FtxConnectorRest
from ftx_connector_ws import FtxConnectorWs
from typing import List
from types_ import WsTicker
import config


def get_funding_rate(symbol: str):
    ts = util.timestamp_now()
    _, fundings = util.get_historical_funding(symbol, ts - 24 * 3600, ts)
    avg = np.mean(fundings)
    return avg * 24 * 365 * 100


class CarryBot:
    def __init__(self):
        self._connector_rest = FtxConnectorRest(config.API_KEY, config.API_SECRET, config.SUB_ACCOUNT)
        self._connector_ws = FtxConnectorWs(config.API_KEY, config.API_SECRET)
        self._connector_ws.process_ticker_cb = self.process_ticker

    def start(self, coins: List[str], expiry: str):
        self._connector_ws.subscribe(coins, expiry)
        self._connector_ws.listen_to_tickers()

    def process_ticker(self, fut: str, perp_ticker: WsTicker, fut_ticker: WsTicker) -> None:
        perp_price = perp_ticker.mark
        fut_price = fut_ticker.mark
        basis = (perp_price - fut_price) / perp_price * 100
        print(f'{fut} basis: {round(basis, 2)}%')


if __name__ == '__main__':
    active_futures = util.get_active_futures_with_expiry()
    _expiry = '0930'
    _coins = [coin for coin in active_futures[_expiry] if coin not in config.BLACKLIST]

    bot = CarryBot()
    bot.start(_coins, _expiry)
