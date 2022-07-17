import pandas as pd
import util
from util import logger
import numpy as np
import datetime as dt
import config
from market_data import CarryMarketData
from account import Account


class CarryBacktesting:
    def __init__(self):
        self.coin = ''
        self.expiration_str = ''
        self.dates = np.array([])
        self.account = None
        self.market_data = None
        self.results_path = ''

    def backtest_carry(self, coin: str, expiration: str, resolution: int, use_cache: bool = True,
                       overwrite_results: bool = False):
        self.coin = coin.upper()
        self.expiration_str = expiration
        self.account = Account(self.coin, self.expiration_str)

        results_folder_path = f'{config.RESULTS_FOLDER}/{expiration}'
        name_path = f'{results_folder_path}/{self.coin}'
        util.create_folder(results_folder_path)
        self.results_path = name_path + '.csv'

        if not overwrite_results and util.file_exists(self.results_path):
            logger.debug(f'results found at {self.results_path}')
        else:
            market_data = CarryMarketData(self.coin, expiration, resolution)
            if use_cache and market_data.read_from_file():
                logger.debug(f'Read market data from {market_data.file_path}')
            else:
                market_data.download()

            self.market_data = market_data
            self._backtest()

            fig = self.account.results.get_figure(self.results_path)
            fig_path = name_path + '.png'
            fig.savefig(fig_path)

        # todo refactor this
        self.account.results.read_from_file(self.results_path)
        return self.account.results.get_final_equity()

    def _backtest(self):
        timestamps = self.market_data.timestamps
        # dates = mdates.num2date(mdates.datestr2num(times))
        # dates = [dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H:%M:%S") for ts in perp_ts]
        dates = [dt.datetime.fromtimestamp(ts).isoformat() for ts in timestamps]
        self.dates = np.array(dates)

        for i, date in enumerate(self.dates):
            perp_price = self.market_data.perp_prices[i]
            fut_price = self.market_data.fut_prices[i]
            funding_rate = self.market_data.funding_rates[i]
            self.account.next(date, perp_price, fut_price, funding_rate)

        if self.account.is_trade_on():
            self.account.close_trade()
            self.account.update_results()

        logger.info(self.account)
        self.account.save_results(self.results_path)


def main():
    coins = util.get_all_futures_coins()
    all_expirations = util.get_all_expirations()

    for expiration in all_expirations:
        results = list()

        for coin in coins:
            fut = f'{coin}-{expiration}'

            expirations = util.get_cached_expirations(expiration)
            if fut in expirations and expirations[fut] == -1:
                continue

            logger.info(fut)
            backtester = CarryBacktesting()

            try:
                profit = backtester.backtest_carry(coin, expiration, 3600, use_cache=True, overwrite_results=False)
            except Exception as e:
                logger.warning(e)
                continue

            results.append({
                'Coin': coin,
                'Profit': profit,
            })

        df = pd.DataFrame(results)
        df.to_csv(f'{config.RESULTS_FOLDER}/{expiration}.csv', index_label=False)

    logger.info('done')


if __name__ == '__main__':
    # CarryBacktesting.check_integrity('./results/1INCH-PERP_1INCH-0624.csv')
    main()
    # c = CarryMarketData('AAVE', '0624', 3600)
    # c.download()
