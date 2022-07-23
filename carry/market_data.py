import numpy as np
from common import util
import pandas as pd
import config


class CarryMarketData:
    def __init__(self, coin: str, expiration: str, resolution: int):
        self.coin = coin
        self.expiration = expiration
        self.resolution = resolution

        self.spot_symbol = util.get_spot_symbol(coin)
        self.perp_symbol = util.get_perp_symbol(coin)
        self.fut_symbol = util.get_future_symbol(coin, expiration)

        self.timestamps = np.array([])
        self.spot_prices = np.array([])
        self.fut_prices = np.array([])
        self.perp_prices = np.array([])
        self.funding_rates = np.array([])

        cache_folder = f'{config.CACHE_FOLDER}/{expiration}'
        util.create_folder(cache_folder)
        self.file_path = f'{cache_folder}/{coin}_{expiration}_{str(resolution)}.csv'

    def download(self):
        expiry_ts = util.get_expiration_ts_from_str(self.expiration)

        # get future prices
        self.timestamps, self.fut_prices = util.get_historical_prices(self.fut_symbol, self.resolution, 0, expiry_ts)

        # start timestamp - skip the first 5 hours
        start_ts = self.timestamps[4]
        self.timestamps, self.fut_prices = self.timestamps[4:], self.fut_prices[4:]

        # todo get spot prices for the same period of the future
        # timestamps_spot, self.spot_prices = util.get_historical_prices(self.spot_symbol, self.resolution, start_ts,
        #                                                                expiry_ts)
        self.spot_prices = np.zeros(len(self.timestamps))

        # get perpetual prices for the same period of the future
        timestamps_perp, self.perp_prices = util.get_historical_prices(self.perp_symbol, self.resolution, start_ts,
                                                                       expiry_ts)

        # get funding rates for the same period of the future
        rates_ts, self.funding_rates = util.get_historical_funding(self.perp_symbol, start_ts, expiry_ts)

        # assert len(self.timestamps) == len(timestamps_spot)
        assert len(self.timestamps) == len(timestamps_perp)
        assert len(self.timestamps) == len(rates_ts)
        # assert self.timestamps.all() == timestamps_spot.all()
        assert self.timestamps.all() == timestamps_perp.all()
        assert self.timestamps.all() == rates_ts.all()

        self.save_cache()

    def save_cache(self):
        try:
            df = pd.DataFrame({
                'Timestamp': self.timestamps,
                'SpotPrice': self.spot_prices,
                'PerpPrice': self.perp_prices,
                'FutPrice': self.fut_prices,
                'FundingRate': self.funding_rates
            })
            df.to_csv(self.file_path, index=False)
        except Exception as e:
            raise Exception(f'Could not save market data cache: {e}')

    def read_from_file(self) -> bool:
        try:
            df = pd.read_csv(self.file_path)  # , parse_dates=['Timestamp'])  # , index_col='Date')
        except FileNotFoundError:
            return False
        self.timestamps = df['Timestamp']
        self.spot_prices = df['SpotPrice']
        self.perp_prices = df['PerpPrice']
        self.fut_prices = df['FutPrice']
        self.funding_rates = df['FundingRate']
        return True
