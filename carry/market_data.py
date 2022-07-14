import numpy as np
import util
import pandas as pd
import config


class CarryMarketData:
    def __init__(self, coin: str, expiration: str, resolution: int):
        self.coin = coin
        self.expiration = expiration
        self.resolution = resolution

        self.perp_name = f'{self.coin}-PERP'
        self.fut_name = f'{self.coin}-{self.expiration}'

        self.timestamps = np.array([])
        self.fut_prices = np.array([])
        self.perp_prices = np.array([])
        self.funding_rates = np.array([])

        self.file_path = f'{config.CACHE_FOLDER}/{coin}_{expiration}_{str(resolution)}.csv'

    def download(self):
        expiry_ts = util.get_future_expiration_ts(self.fut_name)
        if expiry_ts == -1:
            raise Exception(f'Future {self.fut_name} is not found, skip')

        # get future prices
        self.timestamps, self.fut_prices = util.get_historical_prices(self.fut_name, self.resolution, 0, expiry_ts)

        # start timestamp - skip the first 5 hours
        start_ts = self.timestamps[4]
        self.timestamps, self.fut_prices = self.timestamps[4:], self.fut_prices[4:]

        # get perpetual prices for the same period of the future
        timestamps_perp, self.perp_prices = util.get_historical_prices(self.perp_name, self.resolution, start_ts,
                                                                       expiry_ts)

        rates_ts, self.funding_rates = util.get_historical_funding(self.perp_name, start_ts, expiry_ts)

        assert len(self.timestamps) == len(timestamps_perp)
        assert len(self.timestamps) == len(rates_ts)
        assert self.timestamps.all() == timestamps_perp.all()
        assert self.timestamps.all() == rates_ts.all()

        self.save_to_file()

    def save_to_file(self):
        df = pd.DataFrame({
            'Timestamp': self.timestamps,
            'PerpPrices': self.perp_prices,
            'FutPrices': self.fut_prices,
            'FundingRate': self.funding_rates
        })
        util.create_folder(config.CACHE_FOLDER)
        df.to_csv(self.file_path)

    def read_from_file(self) -> bool:
        try:
            df = pd.read_csv(self.file_path)  # , parse_dates=['Timestamp'])  # , index_col='Date')
        except FileNotFoundError:
            return False
        self.timestamps = df['Timestamp']
        self.perp_prices = df['PerpPrices']
        self.fut_prices = df['FutPrices']
        self.funding_rates = df['FundingRate']
        return True