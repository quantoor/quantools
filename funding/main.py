from common import util
import numpy as np


def get_funding_rate(symbol: str):
    ts = util.timestamp_now()
    _, fundings = util.get_historical_funding(symbol, ts - 24 * 3600, ts)
    avg = np.mean(fundings)
    return avg * 24 * 365 * 100


all_perps = util.get_all_perp_symbols()
for perp in all_perps:
    print(perp, end='\r')
    fr = get_funding_rate(perp)
    if fr > 30:
        print(f'{perp}: {round(fr, 2)} %')
