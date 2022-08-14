import threading
from market_data import CarryMarketData
from common import util


def download(coin: str, expiry: str, resolution: int):
    market_data = CarryMarketData(coin, expiry, resolution)
    market_data.download()
    print(f'{coin}-{expiry} done')


coins = util.get_all_futures_coins()
all_expired_futures = util.get_expired_future_symbols()
expiries = util.get_historical_expirations()
threads = []

for expiry in expiries:
    for coin in coins:
        fut = util.get_future_symbol(coin, expiry)

        future_exists = util.future_exists(fut, all_expired_futures)
        if not future_exists:
            continue

        x = threading.Thread(target=download, args=(coin, expiry, 3600,))
        threads.append(x)
        x.start()

for t in threads:
    t.join()

print('done')
