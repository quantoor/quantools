import numpy as np
from common import util
import pandas as pd
import config


class CarryMarketData:
    def __init__(self, coin: str, expiry: str, resolution: int):
        self._coin = coin
        self._expiry = expiry
        self._resolution = resolution

        self._spot_symbol = util.get_spot_symbol(coin)
        self._perp_symbol = util.get_perp_symbol(coin)
        self._fut_symbol = util.get_future_symbol(coin, expiry)

        self.timestamps = np.array([])
        self.spot_prices = np.array([])
        self.fut_prices = np.array([])
        self.perp_prices = np.array([])
        self.funding_rates = np.array([])

        cache_folder = f'{config.CACHE_FOLDER}/{expiry}'
        util.create_folder(cache_folder)
        self.file_path = f'{cache_folder}/{coin}_{expiry}_{str(resolution)}.csv'

    def download(self) -> None:
        expiry_ts = util.get_expiration_ts_from_str(self._expiry)

        # get future prices
        self.timestamps, self.fut_prices = util.get_historical_prices(self._fut_symbol, self._resolution, 0, expiry_ts)

        # start timestamp - skip the first 5 hours
        start_ts = self.timestamps[4]
        self.timestamps, self.fut_prices = self.timestamps[4:], self.fut_prices[4:]

        # todo get spot prices for the same period of the future
        # timestamps_spot, self.spot_prices = util.get_historical_prices(self.spot_symbol, self.resolution, start_ts,
        #                                                                expiry_ts)
        self.spot_prices = np.zeros(len(self.timestamps))

        # get perpetual prices for the same period of the future
        timestamps_perp, self.perp_prices = util.get_historical_prices(self._perp_symbol, self._resolution, start_ts,
                                                                       expiry_ts)

        # get funding rates for the same period of the future
        rates_ts, self.funding_rates = util.get_historical_funding(self._perp_symbol, start_ts, expiry_ts)

        # assert len(self.timestamps) == len(timestamps_spot)
        assert len(self.timestamps) == len(timestamps_perp)
        assert len(self.timestamps) == len(rates_ts)
        # assert self.timestamps.all() == timestamps_spot.all()
        assert self.timestamps.all() == timestamps_perp.all()
        assert self.timestamps.all() == rates_ts.all()

        self._save_cache()

    def _save_cache(self) -> None:
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
