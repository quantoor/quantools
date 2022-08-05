import datetime as dt
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from common.FtxClientRest import FtxClient
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


def iso_date_to_timestamp(iso_date: str) -> int:
    return int(dt.datetime.fromisoformat(iso_date).timestamp())


def file_exists(path: str) -> bool:
    return Path(path).is_file()


def folder_exists(path: str) -> bool:
    return Path(path).is_dir()


def create_folder(path: str) -> None:
    if not folder_exists(path):
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)


def get_files_in_folder(path: str, extension: str = '*') -> List[Path]:
    if extension == '*':
        return [f for f in Path(path).iterdir() if f.is_file()]
    else:
        return [f for f in Path(path).iterdir() if f.is_file() and f.suffix == extension]


def get_folders_in_folder(path: str) -> List[Path]:
    return [f for f in Path(path).iterdir() if f.is_dir()]


client = FtxClient()  # todo refactor this


def get_spot_symbol(coin: str) -> str:
    return f'{coin}/USD'


def get_perp_symbol(coin: str) -> str:
    return f'{coin}-PERP'


def get_future_symbol(coin: str, expiration: str) -> str:
    return f'{coin}-{expiration}'


def get_coin_and_expiration_from_future_symbol(future: str) -> Tuple[str, str]:
    tmp = future.split('-')
    assert len(tmp) == 2
    return tmp[0], tmp[1]


def get_all_spot_symbols() -> List[str]:
    res = client.get_markets()
    markets = []
    for i in res:
        if i['type'] == 'spot' and not i['isEtfMarket'] and not i['restricted']:
            if i['quoteCurrency'] == 'USD':
                markets.append(i['name'])
    return markets


def get_all_perp_symbols() -> List[str]:
    res = client.get_markets()
    markets = []
    for i in res:
        if i['futureType'] == 'perpetual' and not i['isEtfMarket'] and not i['restricted']:
            markets.append(i['name'])
    return markets


def get_historical_prices(instrument: str, resolution: int, start_ts: int, end_ts: int, verbose: bool = False) \
        -> Tuple[np.ndarray, np.ndarray]:
    if verbose:
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
        if verbose:
            print('...', end='')

    if verbose:
        print('done')
    return np.array(timestamps), np.array(prices)


def get_historical_funding(instrument: str, start_ts: int, end_ts: int, verbose: bool = False) \
        -> Tuple[np.ndarray, np.ndarray]:
    if verbose:
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
        if verbose:
            print('...', end='')

    if verbose:
        print('done')
    return np.array(timestamps), np.array(rates)


def get_all_futures_coins() -> List[str]:
    markets = client.get_markets()
    coins = set()
    for i in markets:
        if i['type'] == 'future' and not i['isEtfMarket'] and not i['restricted']:
            coins.add(i['underlying'])
    return sorted(list(coins))


def get_active_futures_with_expiry() -> Dict[str, List[str]]:
    """
    Get active futures with expiry. Returns: Dictionary of expiries to list of coins.
    """
    markets = client.get_markets()
    expiries_dict = {}

    for i in markets:
        if i['futureType'] == 'future' and not i['restricted'] and not i['isEtfMarket']:
            coin, expiry = get_coin_and_expiration_from_future_symbol(i['name'])
            if expiry in expiries_dict:
                expiries_dict[expiry].append(coin)
            else:
                expiries_dict[expiry] = [coin]

    for k, v in expiries_dict.items():
        expiries_dict[k] = sorted(v)

    return expiries_dict


def get_expired_futures() -> Dict[str, List[str]]:
    """
    Get expired futures. Returns: Dictionary of expiries to list of coins.
    """

    coins = get_all_futures_coins()

    expiries = client.get_expired_futures()
    expiries_dict = dict()
    for i in expiries:
        underlying = i['underlying']

        if underlying in coins and i['type'] == 'future':
            name = i['name']
            expiry = name.split('-')[1]

            if expiry not in expiries_dict:
                expiries_dict[expiry] = [underlying]
            else:
                expiries_dict[expiry].append(underlying)

    for k, v in expiries_dict.items():
        expiries_dict[k] = sorted(v)

    return expiries_dict


def get_expiration_date_from_str(expiration: str) -> dt.datetime:
    if len(expiration) == 4:
        month = expiration[:2]
        day = expiration[2:]
        return dt.datetime(dt.datetime.now().year, int(month), int(day))
    else:
        year = expiration[:4]
        month = expiration[4:6]
        day = expiration[6:]
        return dt.datetime(int(year), int(month), int(day))


def get_expiration_ts_from_str(expiration: str) -> int:
    return int(get_expiration_date_from_str(expiration).timestamp())


def get_historical_expirations(start_year: int = 2020) -> List[str]:
    expirations = list(get_expired_futures().keys())
    return [i for i in expirations if get_expiration_date_from_str(i).year >= start_year]


def future_exists(future: str, expired_futures: Dict) -> bool:
    coin, expiration = get_coin_and_expiration_from_future_symbol(future)
    return expiration in expired_futures.keys() and coin in expired_futures[expiration]


def get_all_futures_symbols() -> List[str]:
    res = client.get_all_futures()
    return [f['name'] for f in res if f['type'] == 'future' and not f['perpetual']]


def get_markets() -> Dict[str, Dict]:
    res = client.get_markets()
    return {r['name']: r for r in res if not r['isEtfMarket'] and not r['restricted']}


def round_to_tick(price: float, tick: float) -> float:
    return round(price / tick) * tick


if __name__ == '__main__':
    get_all_spot_symbols()
    print(get_historical_expirations())
    # start_ts = 0
    # end_ts = date_to_timestamp(2022, 6, 24, 0)
    #
    # res = get_historical_prices('BTC-0624', 3600, start_ts, end_ts)
    # print(len(res[0]), len(res[1]))
    # timestamps, perp_prices, fut_prices = get_historical_prices_carry('BTC-0624', 3600)
