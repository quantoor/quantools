import pandas as pd
from common import util
from common.util import logger
import numpy as np
import datetime as dt
import config
from market_data import CarryMarketData
from account import Account
from typing import List
import matplotlib.pyplot as plt


class CarryBacktesting:
    def __init__(self):
        self.account = None
        self._market_data = None

    def backtest_multi(self, expiries: List[str], resolution: int, use_cache: bool = True,
                       overwrite_results: bool = False) -> None:
        coins = util.get_all_futures_coins()
        all_expired_futures = util.get_expired_futures()
        # spot_markets = util.get_all_spot_markets()

        # todo multithread
        for expiry in expiries:
            results = list()

            for coin in coins:
                fut = util.get_future_symbol(coin, expiry)

                future_exists = util.future_exists(fut, all_expired_futures)
                if not future_exists:
                    continue

                logger.info(fut)

                try:
                    profit = self.backtest_single(coin, expiry, resolution, use_cache, overwrite_results)
                except Exception as e:
                    logger.warning(e)
                    continue

                results.append({
                    'Coin': coin,
                    'Profit': profit,
                })

            df = pd.DataFrame(results)
            df.to_csv(f'{config.RESULTS_FOLDER}/{expiry}.csv', index=False)

    def backtest_single(self, coin: str, expiration: str, resolution: int, use_cache: bool = True,
                        overwrite_results: bool = False) -> float:
        coin = coin.upper()
        expiration_str = expiration
        self.account = Account(coin, expiration_str)

        results_folder_path = f'{config.RESULTS_FOLDER}/{expiration}'
        name_path = f'{results_folder_path}/{coin}'
        util.create_folder(results_folder_path)
        results_path = name_path + '.csv'

        if not overwrite_results and util.file_exists(results_path):
            logger.debug(f'Results found at {results_path}')
        else:
            market_data = CarryMarketData(coin, expiration, resolution)
            if use_cache and market_data.read_from_file():
                logger.debug(f'Read market data from {market_data.file_path}')
            else:
                market_data.download()

            self._market_data = market_data
            self._backtest()
            self.account.save_results(results_path)

            fig = self.account.results.get_figure(results_path)
            fig_path = name_path + '.png'
            fig.savefig(fig_path)
            plt.close(fig)

            logger.info(self.account)

        # todo refactor this
        self.account.results.read_from_file(results_path)
        return self.account.results.get_final_equity()

    def _backtest(self) -> None:
        timestamps = self._market_data.timestamps
        # dates = mdates.num2date(mdates.datestr2num(times))
        # dates = [dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H:%M:%S") for ts in perp_ts]
        dates = np.array([dt.datetime.fromtimestamp(ts).isoformat() for ts in timestamps])

        for i, date in enumerate(dates):
            spot_price = self._market_data.spot_prices[i]
            perp_price = self._market_data.perp_prices[i]
            fut_price = self._market_data.fut_prices[i]
            funding_rate = self._market_data.funding_rates[i]
            self.account.next(date, spot_price, perp_price, fut_price, funding_rate)

        if self.account.is_trade_on():
            self.account.close_trade()
            self.account.update_results()


def main():
    all_expiries = util.get_historical_expirations()
    c = CarryBacktesting()
    c.backtest_multi(all_expiries, 3600, use_cache=True, overwrite_results=True)
    logger.info('Done')


if __name__ == '__main__':
    main()
