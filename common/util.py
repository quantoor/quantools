import datetime as dt
import logging
from pathlib import Path
from typing import List, Dict

from common.FtxClientRest import FtxClient
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


def file_exists(path: str) -> bool:
    return Path(path).is_file()


def folder_exists(path: str) -> bool:
    return Path(path).is_dir()


def create_folder(path: str):
    if not folder_exists(path):
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)


client = FtxClient()  # todo refactor this


def get_spot_symbol(coin: str):
    return f'{coin}/USD'


def get_perp_symbol(coin: str):
    return f'{coin}-PERP'


def get_future_symbol(coin: str, expiration: str):
    return f'{coin}-{expiration}'


def get_historical_prices(instrument: str, resolution: int, start_ts: int, end_ts: int):
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

    print('done')
    return np.array(timestamps), np.array(prices)


def get_historical_funding(instrument: str, start_ts: int, end_ts: int):
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

    print('done')
    return np.array(timestamps), np.array(rates)


def get_all_futures_coins() -> List[str]:
    markets = client.get_markets()
    coins = set()
    for i in markets:
        if i['type'] == 'future' and not i['isEtfMarket'] and not i['restricted']:
            coins.add(i['underlying'])
    return sorted(list(coins))


def get_expired_futures() -> Dict:
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


def get_expiration_date_from_str(expiration: str):
    if len(expiration) == 4:
        month = expiration[:2]
        day = expiration[2:]
        return dt.datetime(dt.datetime.now().year, int(month), int(day))
    else:
        year = expiration[:4]
        month = expiration[4:6]
        day = expiration[6:]
        return dt.datetime(int(year), int(month), int(day))


def get_all_expirations(start_year: int = 2020) -> List[str]:
    expirations = list(get_expired_futures().keys())
    return [i for i in expirations if get_expiration_date_from_str(i).year >= start_year]


def get_cached_expirations(expiration: str) -> Dict:
    path = f'./cache/{expiration}/_expirations.csv'  # todo refactor this
    if file_exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    else:
        return {}


def get_future_expiration_ts(future: str) -> int:
    """Returns 0 if the future does not exist."""

    expiration_str = future.split('-')[1]

    # read from cache
    expirations = get_cached_expirations(expiration_str)
    if future in expirations:
        return expirations[future]

    try:
        res = client.get_future(future)
        expiration_ts = iso_date_to_timestamp(res['expiry'])
    except:
        expiration_ts = -1

    expirations[future] = expiration_ts

    # cache value
    create_folder(f'./cache/{expiration_str}')
    with open(f'./cache/{expiration_str}/_expirations.csv', 'w') as f:  # todo refactor this
        f.write(json.dumps(expirations))

    return expiration_ts


if __name__ == '__main__':
    print(get_all_expirations())
    # start_ts = 0
    # end_ts = date_to_timestamp(2022, 6, 24, 0)
    #
    # res = get_historical_prices('BTC-0624', 3600, start_ts, end_ts)
    # print(len(res[0]), len(res[1]))
    # timestamps, perp_prices, fut_prices = get_historical_prices_carry('BTC-0624', 3600)
