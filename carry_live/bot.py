from common import util
import numpy as np
from ftx_connector_rest import FtxConnectorRest
from ftx_connector_ws import FtxConnectorWs


def get_funding_rate(symbol: str):
    ts = util.timestamp_now()
    _, fundings = util.get_historical_funding(symbol, ts - 24 * 3600, ts)
    avg = np.mean(fundings)
    return avg * 24 * 365 * 100


# markets = util.get_markets()
# future_symbols = util.get_all_futures_symbols()
# for future in future_symbols:
#
#     coin, _ = util.get_coin_and_expiration_from_future_symbol(future)
#     perp = util.get_perp_symbol(coin)
#
#     if future not in markets.keys():
#         continue
#
#     future_price = markets[future]['price']
#     perp_price = markets[perp]['price']
#
#     basis = (future_price-perp_price)/perp_price*100
#     if abs(basis) > 1.5:
#         fr = get_funding_rate(perp)
#         print(f'{future}: {round(basis, 2)}%, funding: {round(fr, 2)}%')


if __name__ == '__main__':
    connector_ws = FtxConnectorWs()
    connector_ws.start()
