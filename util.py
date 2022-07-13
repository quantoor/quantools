import datetime as dt
import logging
from pathlib import Path
import pandas as pd
from FtxClientRest import FtxClient
import matplotlib.pyplot as plt
import numpy as np
import json

logger = logging.getLogger("Log")
logger.setLevel(logging.DEBUG)

# console
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def date_to_timestamp(year: int, month: int, day: int, hour: int) -> int:
    date = dt.datetime(year, month, day, hour)
    return int(dt.datetime.timestamp(date))


def timestamp_now() -> int:
    return int(dt.datetime.now().timestamp())


def iso_date_to_timestamp(iso_date: str) -> int:
    return int(dt.datetime.fromisoformat(iso_date).timestamp())


def file_exists(file_path: str) -> bool:
    return Path(file_path).is_file()


def create_folder(path: str):
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)


def load_results(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, parse_dates=['Date'])  # , index_col='Date')
    return df


api_key = 'ZTNWpAc4SsCV4nEICM6nwASP4ao7nHYvLSFzXunj'
api_secret = 'x9tq4yIA27jF83bacZvg-uuFB6Ov6h4n4Ot672QI'
client = FtxClient(api_key, api_secret)


def get_historical_prices(instrument: str, resolution: int, start_ts: int, end_ts: int, plot: bool = False):
    print(f'downloading historical prices of {instrument}...', end='')

    timestamps = []
    prices = []
    first_ts_received = end_ts

    while first_ts_received - resolution > start_ts:
        res = client.get_historical_prices(instrument, resolution, start_ts, first_ts_received - resolution)
        if len(res) == 0:
            break
        first_ts_received = int(res[0]['time'] / 1000)
        for i in reversed(res):
            timestamps.insert(0, int(i['time'] / 1000))
            prices.insert(0, i['open'])
        print('...', end='')

    if plot:
        plt.figure()
        plt.plot(timestamps, prices)
        plt.show()

    print('done')
    return np.array(timestamps), np.array(prices)


def get_historical_funding(instrument: str, start_ts: int, end_ts: int, plot: bool = False):
    print(f'downloading historical funding rate of {instrument}...', end='')

    timestamps = []
    rates = []
    first_ts_received = end_ts

    while first_ts_received - 3600 >= start_ts:
        res = client.get_funding_rates(instrument, start_ts, first_ts_received - 3600)
        first_ts_received = iso_date_to_timestamp(res[-1]['time'])
        for i in res:
            timestamps.insert(0, iso_date_to_timestamp(i['time']))
            rates.insert(0, i['rate'])
        print('...', end='')

    if plot:
        plt.figure()
        plt.plot(timestamps, rates)
        plt.show()

    print('done')
    return np.array(timestamps), np.array(rates)


def get_all_futures_coins():
    markets = client.get_markets()
    coins = set()
    for i in markets:
        if i['type'] == 'future' and not i['isEtfMarket'] and not i['restricted']:
            coins.add(i['underlying'])
    return sorted(list(coins))


def get_expired_futures():
    coins = get_all_futures_coins()

    expirations = client.get_expired_futures()
    expirations_dict = dict()
    for i in expirations:
        underlying = i['underlying']

        if underlying in coins and i['type'] == 'future':
            name = i['name']
            expiration = name.split('-')[1]

            if expiration not in expirations_dict:
                expirations_dict[expiration] = [underlying]
            else:
                expirations_dict[expiration].append(underlying)

    for k, v in expirations_dict.items():
        expirations_dict[k] = sorted(v)

    return expirations_dict


expirations_file = 'cache/_expirations.csv'


def get_cached_expirations():
    if file_exists(expirations_file):
        with open(expirations_file, 'r') as f:
            return json.load(f)
    else:
        return {}


def get_future_expiration_ts(future: str) -> int:
    """Returns 0 if the future does not exist."""

    # read from cache
    expirations = get_cached_expirations()
    if future in expirations:
        return expirations[future]

    try:
        res = client.get_future(future)
        expiration = iso_date_to_timestamp(res['expiry'])
    except:
        expiration = -1

    expirations[future] = expiration

    # cache value
    with open(expirations_file, 'w') as f:
        f.write(json.dumps(expirations))

    return expiration


if __name__ == '__main__':
    print(get_expired_futures())
    # start_ts = 0
    # end_ts = date_to_timestamp(2022, 6, 24, 0)
    #
    # res = get_historical_prices('BTC-0624', 3600, start_ts, end_ts)
    # print(len(res[0]), len(res[1]))
    # timestamps, perp_prices, fut_prices = get_historical_prices_carry('BTC-0624', 3600)
