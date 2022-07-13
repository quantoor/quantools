import pandas as pd
import util
from util import logger
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt
from trading import Position

TRADE_AMOUNT = 100000  # usd
CLOSE_THRESHOLD = 0.1  # %
INIT_OPEN_THRESHOLD = 1.  # %
CACHE_FOLDER = './cache'
RESULTS_FOLDER = './results'


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

        self.file_path = f'{CACHE_FOLDER}/{coin}_{expiration}_{str(resolution)}.csv'

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
        util.create_folder(CACHE_FOLDER)
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


class Account:
    def __init__(self):
        self.perp_position = Position()
        self.fut_position = Position()
        self.tot_profit = 0.

        self.perp_price = 0.
        self.fut_price = 0.
        self.basis = 0.
        self.date = None

        self.trades_open = {}  # {date: basis}
        self.trades_close = {}  # {date: basis}

        self.last_open_basis = 0.
        self.current_open_threshold = INIT_OPEN_THRESHOLD

        self.funding_rate = 0.
        self.funding_paid = 0.
        self.cum_funding_paid = 0.

        self.results = list()

    def __str__(self):
        return f'Total profit: {round(self.tot_profit, 2)}'

    def is_trade_on(self) -> bool:
        return self.perp_position.size != 0 or self.fut_position.size != 0

    def next(self, date: str, perp_price: float, fut_price: float, funding_rate: float):
        self.date = date
        self.perp_price = perp_price
        self.fut_price = fut_price
        self.basis = (perp_price - fut_price) / perp_price * 100

        # check if there is a trade to close
        if self.is_trade_on() and abs(self.basis) < CLOSE_THRESHOLD:
            self.close_trade()

        elif self.is_trade_on() and abs(self.basis - self.last_open_basis) > 5:
            self.close_trade()
            self.last_open_basis = 0
            self.current_open_threshold = self.basis + 1

        # check if there is a trade to open
        elif abs(self.basis) >= self.current_open_threshold:
            self.open_trade()
            self.current_open_threshold = max(self.current_open_threshold + 1., self.basis)
            self.last_open_basis = self.basis

        # compute funding
        self.funding_rate = funding_rate
        self.funding_paid = funding_rate * self.perp_position.size * self.perp_price
        self.cum_funding_paid += self.funding_paid

        self.update_results()

    def update_results(self):
        self.results.append({
            'Date': self.date,
            'PerpPrice': self.perp_price,
            'PerpPosSize': self.perp_position.size,
            'PerpPosEntryPrice': self.perp_position.entry_price,
            'PerpPosPnl': self.perp_position.get_pnl(self.perp_price),
            'FutPrice': self.fut_price,
            'FutPosSize': self.fut_position.size,
            'FutPosEntryPrice': self.fut_position.entry_price,
            'FutPosPnl': self.fut_position.get_pnl(self.fut_price),
            'Basis': self.basis,
            'TradeOpen': True if (self.date in self.trades_open) else False,
            'TradeClose': True if (self.date in self.trades_close) else False,
            'Pnl': self.get_tot_pnl(self.perp_price, self.fut_price),
            'Equity': self.get_equity(self.perp_price, self.fut_price),
            'FundingRate': self.funding_rate,
            'FundingPaid': self.funding_paid,
            'CumFundingPaid': self.cum_funding_paid,
        })

    def open_trade(self):
        perp_amount = TRADE_AMOUNT / self.perp_price
        fut_amount = perp_amount

        if self.basis > 0:
            # sell perp, buy futs
            self.perp_position.update(self.perp_price, -perp_amount)
            self.fut_position.update(self.fut_price, fut_amount)
            print(
                f'{self.date} open trade, sell {round(perp_amount, 2)} perp @ {self.perp_price}, buy {round(fut_amount, 2)} fut @ {self.fut_price}')
        else:
            # buy perp, sell futs
            self.perp_position.update(self.perp_price, perp_amount)
            self.fut_position.update(self.fut_price, -fut_amount)
            print(
                f'{self.date} open trade, buy {round(perp_amount, 2)} perp @ {self.perp_price}, sell {round(fut_amount, 2)} fut @ {self.fut_price}')

        self.trades_open[self.date] = self.basis

    def close_trade(self):
        profit = self.perp_position.get_pnl(self.perp_price) + self.fut_position.get_pnl(self.fut_price)
        self.tot_profit += profit
        self.perp_position.reset()
        self.fut_position.reset()
        self.current_open_threshold = INIT_OPEN_THRESHOLD

        self.trades_close[self.date] = self.basis
        logger.info(f'Profit: {round(profit, 2)}')

    def get_tot_pnl(self, perp_price: float, fut_price: float) -> float:
        return self.perp_position.get_pnl(perp_price) + self.fut_position.get_pnl(fut_price)

    def get_equity(self, perp_price: float, fut_price: float) -> float:
        return self.tot_profit + self.get_tot_pnl(perp_price, fut_price) - self.cum_funding_paid

    def get_net_profit(self):
        return self.tot_profit - self.cum_funding_paid

    def get_results(self) -> pd.DataFrame:
        df = pd.DataFrame(self.results)
        # df['Timestamp'] = [dt.datetime.fromtimestamp(ts) for ts in df['Date']]  # add a column with a date format
        # df.set_index('Timestamp', inplace=True)
        return df

    def save_results(self, path: str):
        results = self.get_results()
        results.to_csv(path)


class CarryBacktesting:
    def __init__(self):
        self.coin = ''
        self.expiration_str = ''
        self.dates = np.array([])
        self.perp_prices = np.array([])
        self.fut_prices = np.array([])
        self.funding_rates = np.array([])
        self.account = Account()

        self.results_path = ''

    def backtest_carry(self, coin: str, expiration: str, resolution: int,
                       use_cache: bool = True,
                       overwrite_results: bool = False):
        self.coin = coin.upper()
        self.expiration_str = expiration

        results_folder_path = f'{RESULTS_FOLDER}/{expiration}'
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

            timestamps = market_data.timestamps
            self.perp_prices = market_data.perp_prices
            self.fut_prices = market_data.fut_prices
            self.funding_rates = market_data.funding_rates

            # dates = mdates.num2date(mdates.datestr2num(times))
            # dates = [dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H:%M:%S") for ts in perp_ts]
            dates = [dt.datetime.fromtimestamp(ts).isoformat() for ts in timestamps]
            self.dates = np.array(dates)
            self._backtest()

        fig = self.get_results_plot_figure()
        fig_path = name_path + '.png'
        fig.savefig(fig_path)

        # todo load from file when reading results. Also create class results
        return self.account.get_net_profit()

    def _backtest(self):
        for i, date in enumerate(self.dates):
            perp_price = self.perp_prices[i]
            fut_price = self.fut_prices[i]
            funding_rate = self.funding_rates[i]
            self.account.next(date, perp_price, fut_price, funding_rate)

        if self.account.is_trade_on():
            self.account.close_trade()
            self.account.update_results()

        logger.info(self.account)
        self.account.save_results(self.results_path)

    def get_results_plot_figure(self) -> matplotlib.figure:
        logger.debug('plotting')

        df = util.load_results(self.results_path)

        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 6), sharex='col')
        fig.suptitle(f'{self.coin} - {self.expiration_str}')

        dates = df['Date']
        perp_prices = df['PerpPrice']
        fut_prices = df['FutPrice']
        basis = df['Basis']
        trades_open_dict = {date: basis for date, basis, trade_open in zip(df['Date'], df['Basis'], df['TradeOpen'])
                            if trade_open}
        trades_close_dict = {date: basis for date, basis, trade_close in
                             zip(df['Date'], df['Basis'], df['TradeClose']) if trade_close}
        pnl = df['Pnl']
        equity = df['Equity']
        funding_rate = df['FundingRate']
        funding_paid = df['FundingPaid']

        # ax1
        ax1.plot(dates, perp_prices, linewidth=1)
        ax1.plot(dates, fut_prices, linewidth=1)
        ax1.legend(['perp', 'fut'])
        ax1.set_ylabel('Price $', labelpad=10)
        ax1.grid()

        # ax2
        ax2.plot(dates, basis, linewidth=1)  # plot basis
        ax2.plot(trades_open_dict.keys(), trades_open_dict.values(), 'ro', mfc='none')  # plot open trades
        ax2.plot(trades_close_dict.keys(), trades_close_dict.values(), 'rx')  # plot close trades
        ax2.legend(['basis', 'open', 'close'])
        ax2.set_ylabel('Basis %')
        ax2.grid()

        # ax3
        lns1 = ax3.plot(dates, equity, linewidth=1, label='equity')
        # ax3.legend(['equity'])
        ax3.set_ylabel('Equity $', labelpad=10)
        ax3.grid()

        ax3_ = ax3.twinx()
        lns2 = ax3_.plot(dates, pnl, color='orange', linewidth=0.3, label='pnl')
        ax3_.set_ylabel('Pnl $', labelpad=10)

        lns = lns1 + lns2
        labs = [label.get_label() for label in lns]
        ax3.legend(lns, labs)

        # ax4
        lns1 = ax4.plot(dates, funding_paid, linewidth=1, label='funding paid')
        # ax4.fill_between(dates, 0, funding_paid, alpha=0.5, where=funding_paid > 0, facecolor='r')
        # ax4.fill_between(dates, 0, funding_paid, alpha=0.5, where=funding_paid < 0, facecolor='g')
        # ax4.legend(['funding rate', 'funding paid'])
        ax4.set_ylabel('Funding paid $', labelpad=10)
        ax4.grid()

        ax4_ = ax4.twinx()
        lns2 = ax4_.plot(dates, funding_rate * 100, color='orange', linewidth=0.3, label='funding rate')
        ax4_.set_ylabel('Funding rate %', labelpad=10)

        lns = lns1 + lns2
        labs = [label.get_label() for label in lns]
        ax4.legend(lns, labs)

        fig.autofmt_xdate()
        fig.tight_layout()
        return fig

    @staticmethod
    def check_integrity(file_path: str):
        df = util.load_results(file_path)

        for i in range(1, len(df.index)):
            line = i + 1
            date, date_ = df['Date'][i], df['Date'][i - 1]
            perp_price, perp_price_ = df['PerpPrice'][i], df['PerpPrice'][i - 1]
            perp_pos_size, perp_pos_size_ = df['PerpPosSize'][i], df['PerpPosSize'][i - 1]
            perp_pos_entry_price, perp_pos_entry_price_ = df['PerpPosEntryPrice'][i], df['PerpPosEntryPrice'][i - 1]
            perp_pos_pnl, perp_pos_pnl_ = df['PerpPosPnl'][i], df['PerpPosPnl'][i - 1]
            fut_price, fut_price_ = df['FutPrice'][i], df['FutPrice'][i - 1]
            fut_pos_size, fut_pos_size_ = df['FutPosSize'][i], df['FutPosSize'][i - 1]
            fut_pos_entry_price, fut_pos_entry_price_ = df['FutPosEntryPrice'][i], df['FutPosEntryPrice'][i - 1]
            fut_pos_pnl, fut_pos_pnl_ = df['FutPosPnl'][i], df['FutPosPnl'][i - 1]
            basis, basis_ = df['Basis'][i], df['Basis'][i - 1]
            trade_open = df['TradeOpen'][i]
            trade_close = df['TradeClose'][i]
            pnl, pnl_ = df['Pnl'][i], df['Pnl'][i - 1]
            equity, equity_ = df['Equity'][i], df['Equity'][i - 1]
            funding_rate, funding_rate_ = df['FundingRate'][i], df['FundingRate'][i - 1]
            funding_paid, funding_paid_ = df['FundingPaid'][i], df['FundingPaid'][i - 1]
            cum_funding_paid, cum_funding_paid_ = df['CumFundingPaid'][i], df['CumFundingPaid'][i - 1]

            assert not (trade_open and trade_close)
            if trade_open:
                pass
            elif trade_close:
                pass
            else:
                # position size and entry prices did not change
                np.testing.assert_equal(perp_pos_size, perp_pos_size_)
                np.testing.assert_equal(perp_pos_entry_price, perp_pos_entry_price_)
                np.testing.assert_equal(fut_pos_size, fut_pos_size_)
                np.testing.assert_equal(fut_pos_entry_price, fut_pos_entry_price_)

                # check
                d_perp_price = perp_price - perp_price_
                d_perp_pos_pnl = perp_pos_pnl - perp_pos_pnl_
                np.testing.assert_almost_equal(d_perp_price * perp_pos_size, d_perp_pos_pnl)

                d_fut_price = fut_price - fut_price_
                d_fut_pos_pnl = fut_pos_pnl - fut_pos_pnl_
                np.testing.assert_almost_equal(d_fut_price * fut_pos_size, d_fut_pos_pnl)

                # pnl & equity
                d_pnl = pnl - pnl_
                np.testing.assert_almost_equal(perp_pos_pnl + fut_pos_pnl, pnl, err_msg=f'at line {line}')
                np.testing.assert_almost_equal(equity_ + d_pnl - funding_paid, equity, err_msg=f'at line {line}')

                # funding rate paid
                np.testing.assert_almost_equal(perp_pos_size * funding_rate * perp_price, funding_paid)

                # cumulative funding rate paid
                np.testing.assert_almost_equal(cum_funding_paid_ + funding_paid, cum_funding_paid)

            # if i > 5:
            #     break


def main():
    coins = util.get_all_futures_coins()
    expiration = '0624'

    results = list()

    for coin in coins:
        fut = f'{coin}-{expiration}'
        expirations = util.get_cached_expirations()
        if fut in expirations and expirations[fut] == -1:
            continue

        backtester = CarryBacktesting()

        try:
            profit = backtester.backtest_carry(coin, expiration, 3600,
                                               use_cache=True,
                                               overwrite_results=False)
        except Exception as e:
            logger.warning(e)
            continue

        results.append({
            'Coin': coin,
            'Profit': profit,
        })

    df = pd.DataFrame(results)
    df.to_csv(f'{RESULTS_FOLDER}/{expiration}.csv')
    # plt.show()
    logger.info('done')


if __name__ == '__main__':
    # CarryBacktesting.check_integrity('./results/1INCH-PERP_1INCH-0624.csv')
    main()
    # c = CarryMarketData('AAVE', '0624', 3600)
    # c.download()
