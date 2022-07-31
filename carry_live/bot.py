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
        self._expiry: str = ''

    def start(self, coins: List[str], expiry: str):
        self._expiry = expiry
        self._connector_ws.subscribe(coins, expiry)
        self._connector_ws.listen_to_tickers(config.REFRESH_TIME)

    def process_ticker(self, coin: str, perp_ticker: WsTicker, fut_ticker: WsTicker) -> None:
        perp_price = perp_ticker.mark
        fut_price = fut_ticker.mark
        basis = (perp_price - fut_price) / perp_price * 100
        print(f'{coin} basis: {round(basis, 2)}%')

        # perp_symbol = util.get_perp_symbol(coin)
        # fut_symbol = util.get_future_symbol(coin, self._expiry)

        # self._connector_rest.buy_limit(perp_symbol, 0.9 * perp_price, 0.001)
        # self._connector_rest.sell_limit(perp_symbol, 1.1 * perp_price, 0.001)
        # exit()


if __name__ == '__main__':
    active_futures = util.get_active_futures_with_expiry()
    _expiry = '0930'
    _coins = [coin for coin in active_futures[_expiry] if coin not in config.BLACKLIST]

    bot = CarryBot()
    res = bot._connector_rest.get_open_orders()
    print(res)
    bot.start(['BTC'], _expiry)
