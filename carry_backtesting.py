import pandas as pd
import util
from util import logger
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import datetime as dt

COIN = '1INCH'
TRADE_AMOUNT = 100000  # usd
CLOSE_THRESHOLD = 0.1  # %
INIT_OPEN_THRESHOLD = 1.  # %
RESULTS_FOLDER = './results'


class Position:
    def __init__(self, entry_price=None, size=0):
        self.entry_price = entry_price
        self.size = size

    def __str__(self):
        return f'Entry price: {self.entry_price}, size: {self.size}'

    def update(self, price: float, size: float):
        if self.entry_price is None:
            self.entry_price = price
        else:
            self.entry_price = (self.entry_price * self.size + price * size) / (self.size + size)
        self.size += size

    def reset(self):
        self.entry_price = None
        self.size = 0

    def get_pnl(self, price: float) -> float:
        if self.entry_price is None or price == self.entry_price:
            return 0
        return price * self.size * (price - self.entry_price) / self.entry_price

    def notional_value(self, price: float) -> float:
        return abs(price * self.size)


class Account:
    def __init__(self, init_balance: float):
        self.perp_position = Position()
        self.future_position = Position()
        self.tot_profit = init_balance

        self.perp_price = 0.
        self.future_price = 0.
        self.basis = 0.
        self.date = None

        self.trades_open = {}  # {date: basis}
        self.trades_close = {}  # {date: basis}

        self.last_open_basis = 0.
        self.current_open_threshold = INIT_OPEN_THRESHOLD

        self._results = []

    def __str__(self):
        return f'Total profit: {round(self.tot_profit, 2)}'

    def is_trade_on(self) -> bool:
        return self.perp_position.size != 0 or self.future_position.size != 0

    def next(self, date: str, perp_price: float, future_price: float, funding_rate: float):
        # todo flowchart

        funding_paid = funding_rate * self.perp_position.size

        self.date = date
        self.perp_price = perp_price
        self.future_price = future_price
        self.basis = (perp_price - future_price) / perp_price * 100

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

        # append new row
        self._results.append({
            'Date': self.date,
            'PerpPrice': self.perp_price,
            'PerpPosSize': self.perp_position.size,
            'PerpPosEntryPrice': self.perp_position.entry_price,
            'PerpPosPnl': self.perp_position.get_pnl(self.perp_price),
            'FuturePrice': self.future_price,
            'FuturePosSize': self.future_position.size,
            'FuturePosEntryPrice': self.future_position.entry_price,
            'FuturePosPnl': self.future_position.get_pnl(self.future_price),
            'Basis': self.basis,
            'TradeOpen': True if (self.date in self.trades_open) else False,
            'TradeClose': True if (self.date in self.trades_close) else False,
            'Equity': self.get_equity(self.perp_price, self.future_price),
            'FundingRate': funding_rate,
            'FundingPaid': funding_paid,
        })

    def open_trade(self):
        perp_amount = TRADE_AMOUNT / self.perp_price
        future_amount = perp_amount

        if self.basis > 0:
            # sell perp, buy futures
            self.perp_position.update(self.perp_price, -perp_amount)
            self.future_position.update(self.future_price, future_amount)
            print(
                f'{self.date} open trade, sell {round(perp_amount, 2)} perp @ {self.perp_price}, buy {round(future_amount, 2)} future @ {self.future_price}')
        else:
            # buy perp, sell futures
            self.perp_position.update(self.perp_price, perp_amount)
            self.future_position.update(self.future_price, -future_amount)
            print(
                f'{self.date} open trade, buy {round(perp_amount, 2)} perp @ {self.perp_price}, sell {round(future_amount, 2)} future @ {self.future_price}')

        self.trades_open[self.date] = self.basis

    def close_trade(self):
        if self.perp_position.size > 0:
            print(
                f'{self.date} close trade, sell {round(self.perp_position.size, 2)} perp @ {self.perp_price} pnl {self.perp_position.get_pnl(self.perp_price)},'
                f' buy {round(self.future_position.size, 2)} future @ {self.future_price} pnl {self.future_position.get_pnl(self.future_price)}')
        else:
            print(
                f'{self.date} close trade, buy {round(self.perp_position.size, 2)} perp @ {self.perp_price} pnl {self.perp_position.get_pnl(self.perp_price)},'
                f' sell {round(self.future_position.size, 2)} future @ {self.future_price} pnl {self.future_position.get_pnl(self.future_price)}')

        profit = self.perp_position.get_pnl(self.perp_price) + self.future_position.get_pnl(self.future_price)
        self.tot_profit += profit
        self.perp_position.reset()
        self.future_position.reset()
        self.current_open_threshold = INIT_OPEN_THRESHOLD

        self.trades_close[self.date] = self.basis
        logger.info(f'Profit: {round(profit, 2)}')

    def get_equity(self, perp_price: float, future_price: float) -> float:
        return self.tot_profit + self.perp_position.get_pnl(perp_price) + self.future_position.get_pnl(future_price)

    def get_results(self) -> pd.DataFrame:
        df = pd.DataFrame(self._results)
        # df['Timestamp'] = [dt.datetime.fromtimestamp(ts) for ts in df['Date']]  # add a column with a date format
        # df.set_index('Timestamp', inplace=True)
        return df


class CarryBacktesting:
    def __init__(self):
        self.dates = np.array([])
        self.perp_prices = np.array([])
        self.future_prices = np.array([])
        self.funding_rates = np.array([])
        self.account = Account(0)

        self.results_path = ''

    def backtest_carry(self, perp: str, future: str, resolution: int, start_ts: int, end_ts: int,
                       load_results: bool = False):
        self.results_path = f'{RESULTS_FOLDER}/{perp}_{future}.csv'

        if load_results and util.file_exists(self.results_path):
            logger.info(f'results found at {self.results_path}')
        else:
            perp_ts, self.perp_prices = util.get_historical_prices(perp, resolution, start_ts, end_ts)
            future_ts, self.future_prices = util.get_historical_prices(future, resolution, start_ts, end_ts)
            rates_ts, self.funding_rates = util.get_historical_funding(perp, start_ts, end_ts)

            assert perp_ts.all() == future_ts.all()
            assert len(self.perp_prices) == len(self.future_prices)
            assert perp_ts.all() == rates_ts.all()
            assert len(self.perp_prices) == len(self.funding_rates)

            # dates = mdates.num2date(mdates.datestr2num(times))
            # dates = [dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H:%M:%S") for ts in perp_ts]
            dates = [dt.datetime.fromtimestamp(ts).isoformat() for ts in perp_ts]
            self.dates = np.array(dates)
            self._backtest()

        self._plot()

    def _backtest(self):
        for i, date in enumerate(self.dates):
            perp_price = self.perp_prices[i]
            future_price = self.future_prices[i]
            funding_rate = self.funding_rates[i]
            self.account.next(date, perp_price, future_price, funding_rate)

        if self.account.is_trade_on():
            self.account.close_trade()

        logger.info(self.account)

        results = self.account.get_results()
        util.create_folder(RESULTS_FOLDER)
        results.to_csv(self.results_path)

    def _plot(self):
        logger.info('plotting')

        df = util.load_results(self.results_path)

        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 6), sharex='col')
        fig.suptitle(COIN)

        dates = df['Date']
        perp_prices = df['PerpPrice']
        future_prices = df['FuturePrice']
        basis = df['Basis']
        trades_open_dict = {date: basis for date, basis, trade_open in zip(df['Date'], df['Basis'], df['TradeOpen']) if
                            trade_open}
        trades_close_dict = {date: basis for date, basis, trade_close in zip(df['Date'], df['Basis'], df['TradeClose'])
                             if trade_close}
        equity = df['Equity']
        funding_rate = df['FundingRate']
        funding_paid = df['FundingPaid']

        # ax1
        ax1.plot(dates, perp_prices, linewidth=1)
        ax1.plot(dates, future_prices, linewidth=1)
        ax1.legend(['perp', 'future'])
        ax1.set_ylabel('$')
        ax1.grid()

        # ax2
        ax2.plot(dates, basis, linewidth=1)  # plot basis
        ax2.plot(trades_open_dict.keys(), trades_open_dict.values(), 'ro', mfc='none')  # plot open trades
        ax2.plot(trades_close_dict.keys(), trades_close_dict.values(), 'rx')  # plot close trades
        ax2.legend(['basis', 'open', 'close'])
        ax2.set_ylabel('%')
        ax2.grid()

        # ax3
        ax3.plot(dates, equity, linewidth=1)
        ax3.legend(['equity'])
        ax3.set_ylabel('$')
        ax3.grid()

        # ax4
        ax4.plot(dates, funding_rate, linewidth=1)
        ax4.plot(dates, funding_paid, linewidth=1)
        ax4.legend(['funding rate', 'funding paid'])
        ax4.set_ylabel('$')
        ax4.grid()

        fig.autofmt_xdate()
        plt.show()


if __name__ == '__main__':
    _resolution = 3600
    _start_ts = util.date_to_timestamp(2022, 3, 20, 0)
    _end_ts = util.date_to_timestamp(2022, 6, 24, 0)

    backtester = CarryBacktesting()
    backtester.backtest_carry(f'{COIN}-PERP', f'{COIN}-0624', _resolution, _start_ts, _end_ts)
    logger.info('done')

    # def carry(self):
    #     futures = self.client.get_all_futures()
    #
    #     for i in futures:
    #         if i['type'] == 'future' and not i['perpetual']:
    #
    #             spotSymbol = i['underlying']
    #             futureSymbol = i['name']
    #
    #             try:
    #                 ul_market = self.client.get_single_market(f'{spotSymbol}/USD')
    #             except Exception as e:
    #                 print(e)
    #                 continue
    #
    #             ul_price = ul_market['price']
    #             future_price = i['mark']
    #
    #             # higher = max(ul_price, futurePrice)
    #             # lower = min(ul_price, futurePrice)
    #             basis = (future_price - ul_price) / ul_price * 100
    #
    #             if abs(basis) > 3:
    #                 print(f'{spotSymbol}: spot {ul_price}, {futureSymbol} {future_price}, basis {round(basis, 1)} %')
    #
    # def analyze_carry(self):
    #     # mean rev: YFI SUSHI FTM AAVE
    #     # crazy: WAVES GST GMT BAL AXS
    #
    #     coins = {}  # {'coin': [a,b,c]}
    #
    #     markets = self.client.get_markets()
    #     # expired_futures = client.get_expired_futures()
    #     # expired_futures_btc = [i for i in expired_futures if i['underlying'] == 'BTC' and i['type'] == 'future']
    #
    #     for instrument in markets:
    #
    #         if instrument['quoteCurrency'] not in ['USD', None]:
    #             continue
    #         if instrument['futureType'] == 'move':
    #             continue
    #         if instrument['restricted']:
    #             continue
    #
    #         ul_name = instrument['underlying']
    #         if ul_name is None:
    #             ul_name = instrument['baseCurrency']
    #
    #         if ul_name in ['BTC', 'CEL', 'DOGE', 'ETH', 'XRP', 'USDT']:
    #             continue
    #
    #         if ul_name in coins:
    #             coins[ul_name].append(instrument)
    #         else:
    #             coins[ul_name] = [instrument]
    #
    #     coins = {key: value for (key, value) in coins.items() if len(value) > 2}
    #
    #     start_timestamp = util.date_to_timestamp_sec(2022, 6, 1, 0)
    #     end_timestamp = util.timestamp_now()
    #
    #     for coin in coins:
    #         print(coin)
    #         # spot_prices = client.get_historical_prices(f'{coin}/USD', 3600, start_timestamp, end_timestamp)
    #         perp_prices = self.client.get_historical_prices(f'{coin}-PERP', 3600, start_timestamp, end_timestamp)
    #         future_prices = self.client.get_historical_prices(f'{coin}-0930', 3600, start_timestamp, end_timestamp)
    #
    #         N = len(future_prices)
    #         perp_prices = perp_prices[len(perp_prices) - N:]
    #
    #         times = [price['startTime'] for price in perp_prices]
    #         dates = mdates.num2date(mdates.datestr2num(times))
    #         dates = np.array(dates)
    #
    #         # spot_prices = np.array([price['close'] for price in spot_prices])
    #         perp_prices = np.array([price['close'] for price in perp_prices])
    #         future_prices = np.array([price['close'] for price in future_prices])
    #
    #         if len(perp_prices) != len(future_prices):
    #             print('skip')
    #             continue
    #
    #         fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex='col')
    #         fig.suptitle(coin)
    #
    #         # ax.plot(dates, spot_prices)
    #         ax1.plot(dates, perp_prices)
    #         ax1.plot(dates, future_prices)
    #         ax1.legend(['perp', 'future'])
    #         ax1.set_ylabel('$')
    #         ax1.grid()
    #
    #         ax2.plot(dates, (perp_prices - future_prices) / perp_prices * 100)
    #         ax2.set_ylabel('%')
    #         ax2.grid()
    #
    #         fig.autofmt_xdate()
    #
    #     plt.show()
    #
    # def plot_carry_expired(self):
    #     print('start')
    #
    #     coin = 'AAVE'
    #     resolution = 14400
    #
    #     start_timestamp = util.date_to_timestamp_sec(2022, 3, 20, 0)
    #     end_timestamp = util.date_to_timestamp_sec(2022, 6, 24, 0)
    #
    #     print('getting perp prices')
    #     perp_prices = self.client.get_historical_prices(f'{coin}-PERP', resolution, start_timestamp, end_timestamp)
    #     print('getting future prices')
    #     future_prices = self.client.get_historical_prices(f'{coin}-0624', resolution, start_timestamp, end_timestamp)
    #
    #     times = [price['startTime'] for price in perp_prices]
    #     print(len(perp_prices), len(future_prices))
    #
    #     dates = mdates.num2date(mdates.datestr2num(times))
    #     dates = np.array(dates)
    #
    #     perp_prices = np.array([price['close'] for price in perp_prices])
    #     future_prices = np.array([price['close'] for price in future_prices])
    #
    #     print('plotting')
    #     fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex='col')
    #     fig.suptitle(coin)
    #
    #     ax1.plot(dates, perp_prices, linewidth=1)
    #     ax1.plot(dates, future_prices, linewidth=1)
    #     ax1.legend(['perp', 'future'])
    #     ax1.set_ylabel('$')
    #     ax1.grid()
    #
    #     ax2.plot(dates, (perp_prices - future_prices) / perp_prices * 100)
    #     ax2.set_ylabel('%')
    #     ax2.grid()
    #
    #     fig.autofmt_xdate()
    #     plt.show()
