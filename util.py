import datetime as dt
import logging
from pathlib import Path
import pandas as pd
from FtxClientRest import FtxClient
import matplotlib.pyplot as plt
import numpy as np

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

    while first_ts_received - 3600 > start_ts:
        res = client.get_funding_rates(instrument, start_ts, first_ts_received - 3600)
        first_ts_received = int(dt.datetime.fromisoformat(res[-1]['time']).timestamp())
        for i in res:
            timestamps.insert(0, int(dt.datetime.fromisoformat(i['time']).timestamp()))
            rates.insert(0, i['rate'])
        print('...', end='')

    if plot:
        plt.figure()
        plt.plot(timestamps, rates)
        plt.show()

    print('done')
    return np.array(timestamps), np.array(rates)
