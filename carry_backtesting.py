import util
from FtxClientRest import FtxClient
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

api_key = 'ZTNWpAc4SsCV4nEICM6nwASP4ao7nHYvLSFzXunj'
api_secret = 'x9tq4yIA27jF83bacZvg-uuFB6Ov6h4n4Ot672QI'

COIN = '1INCH'
TRADE_AMOUNT = 1000  # usd
MIN_THRESHOLD = 0.1  # %
MAX_THRESHOLD = 1  # %


class Position:
    """ The open position is defined by an entry price and a position size.
        ROE and PNL can be computed given the mark price.
    """

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

    def _get_roe(self, price: float) -> float:
        return (price - self.entry_price) / self.entry_price * 100 * self.size / abs(self.size)

    def get_pnl(self, price: float) -> float:
        pnl = price * abs(self.size) * self._get_roe(price) / 100
        return round(pnl, 2)
        # return price * self.size * (price - self.entry_price) / self.entry_price

    def notional_value(self, price: float) -> float:
        return abs(price * self.size)


class Account:
    def __init__(self, init_balance: float):
        self.perp_position = Position()
        self.future_position = Position()
        self.usd_balance = init_balance

        self.open_basis = 0

        self.perp_price = 0.
        self.future_price = 0.
        self.basis = 0.
        self.date = None
        self.trades_open = {}  # {date: basis}
        self.trades_close = {}  # {date: basis}

    def __str__(self):
        return f'Final balance: {self.usd_balance}'

    def _is_trade_on(self) -> bool:
        return self.perp_position.size != 0 or self.future_position.size != 0

    def trade(self, date: str, perp_price: float, future_price: float):
        # todo flowchart

        self.date = date
        self.perp_price = perp_price
        self.future_price = future_price
        self.basis = (perp_price - future_price) / perp_price * 100

        # check if there is a trade to close
        if self._is_trade_on() and abs(self.basis) < MIN_THRESHOLD:
            self.close_trade()
            self.trades_close[date] = self.basis
        # check if there is a trade to open
        elif not self._is_trade_on() and abs(self.basis) >= MAX_THRESHOLD:
            self.open_trade()
            self.trades_open[date] = self.basis
            self.open_basis = self.basis

        elif self._is_trade_on() and abs(self.basis - self.open_basis) > 1:
            self.close_trade()
            self.trades_close[date] = self.basis
            self.open_basis = 0

    def open_trade(self):
        perp_amount = TRADE_AMOUNT / self.perp_price
        future_amount = perp_amount
        # self.usd_balance -= TRADE_AMOUNT + future_amount * self.future_price

        if self.basis > 0:
            # sell perp, buy futures
            self.perp_position.update(self.perp_price, -perp_amount)
            self.future_position.update(self.future_price, future_amount)
            print(
                f'{self.date} open trade, sell {round(perp_amount, 2)} perp @ {self.perp_price}, buy {round(future_amount, 2)} future @ {self.future_price}. Balance {self.usd_balance}')
        else:
            # buy perp, sell futures
            self.perp_position.update(self.perp_price, perp_amount)
            self.future_position.update(self.future_price, -future_amount)
            print(
                f'{self.date} open trade, buy {round(perp_amount, 2)} perp @ {self.perp_price}, sell {round(future_amount, 2)} future @ {self.future_price}. Balance {self.usd_balance}')

    def close_trade(self):
        if self.perp_position.size > 0:
            print(
                f'{self.date} close trade, sell {round(self.perp_position.size, 2)} perp @ {self.perp_price} pnl {self.perp_position.get_pnl(self.perp_price)},'
                f' buy {round(self.future_position.size, 2)} future @ {self.future_price} pnl {self.future_position.get_pnl(self.future_price)}. ',
                end=' ')
        else:
            print(
                f'{self.date} close trade, buy {round(self.perp_position.size, 2)} perp @ {self.perp_price} pnl {self.perp_position.get_pnl(self.perp_price)},'
                f' sell {round(self.future_position.size, 2)} future @ {self.future_price} pnl {self.future_position.get_pnl(self.future_price)}. ',
                end='')
        profit = self.perp_position.get_pnl(self.perp_price) + self.future_position.get_pnl(self.future_price)
        self.usd_balance += profit
        self.perp_position.reset()
        self.future_position.reset()
        print(f'Profit: {round(profit, 2)}. Balance: {round(self.usd_balance, 2)}')

        self.perp_position.entry_price = None
        self.perp_position.size = 0
        self.future_position.entry_price = None
        self.future_position.size = 0

    def get_equity(self, perp_price: float, future_price: float) -> float:
        return self.usd_balance + self.perp_position.get_pnl(perp_price) + self.future_position.get_pnl(future_price)


class CarryBacktesting:
    def __init__(self):
        self.client = FtxClient(api_key, api_secret)

        self.dates = np.array([])
        self.perp_prices = np.array([])
        self.future_prices = np.array([])
        self.account = Account(1000)

    def carry(self):
        futures = self.client.get_all_futures()

        for i in futures:
            if i['type'] == 'future' and not i['perpetual']:

                spotSymbol = i['underlying']
                futureSymbol = i['name']

                try:
                    ul_market = self.client.get_single_market(f'{spotSymbol}/USD')
                except Exception as e:
                    print(e)
                    continue

                ul_price = ul_market['price']
                future_price = i['mark']

                # higher = max(ul_price, futurePrice)
                # lower = min(ul_price, futurePrice)
                basis = (future_price - ul_price) / ul_price * 100

                if abs(basis) > 3:
                    print(f'{spotSymbol}: spot {ul_price}, {futureSymbol} {future_price}, basis {round(basis, 1)} %')

    def analyze_carry(self):
        # mean rev: YFI SUSHI FTM AAVE
        # crazy: WAVES GST GMT BAL AXS

        coins = {}  # {'coin': [a,b,c]}

        markets = self.client.get_markets()
        # expired_futures = client.get_expired_futures()
        # expired_futures_btc = [i for i in expired_futures if i['underlying'] == 'BTC' and i['type'] == 'future']

        for instrument in markets:

            if instrument['quoteCurrency'] not in ['USD', None]:
                continue
            if instrument['futureType'] == 'move':
                continue
            if instrument['restricted']:
                continue

            ul_name = instrument['underlying']
            if ul_name is None:
                ul_name = instrument['baseCurrency']

            if ul_name in ['BTC', 'CEL', 'DOGE', 'ETH', 'XRP', 'USDT']:
                continue

            if ul_name in coins:
                coins[ul_name].append(instrument)
            else:
                coins[ul_name] = [instrument]

        coins = {key: value for (key, value) in coins.items() if len(value) > 2}

        start_timestamp = util.date_to_timestamp_sec(2022, 6, 1, 0)
        end_timestamp = util.timestamp_now()

        for coin in coins:
            print(coin)
            # spot_prices = client.get_historical_prices(f'{coin}/USD', 3600, start_timestamp, end_timestamp)
            perp_prices = self.client.get_historical_prices(f'{coin}-PERP', 3600, start_timestamp, end_timestamp)
            future_prices = self.client.get_historical_prices(f'{coin}-0930', 3600, start_timestamp, end_timestamp)

            N = len(future_prices)
            perp_prices = perp_prices[len(perp_prices) - N:]

            times = [price['startTime'] for price in perp_prices]
            dates = mdates.num2date(mdates.datestr2num(times))
            dates = np.array(dates)

            # spot_prices = np.array([price['close'] for price in spot_prices])
            perp_prices = np.array([price['close'] for price in perp_prices])
            future_prices = np.array([price['close'] for price in future_prices])

            if len(perp_prices) != len(future_prices):
                print('skip')
                continue

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex='col')
            fig.suptitle(coin)

            # ax.plot(dates, spot_prices)
            ax1.plot(dates, perp_prices)
            ax1.plot(dates, future_prices)
            ax1.legend(['perp', 'future'])
            ax1.set_ylabel('$')
            ax1.grid()

            ax2.plot(dates, (perp_prices - future_prices) / perp_prices * 100)
            ax2.set_ylabel('%')
            ax2.grid()

            fig.autofmt_xdate()

        plt.show()

    def plot_carry_expired(self):
        print('start')

        coin = 'AAVE'
        resolution = 14400

        start_timestamp = util.date_to_timestamp_sec(2022, 3, 20, 0)
        end_timestamp = util.date_to_timestamp_sec(2022, 6, 24, 0)

        print('getting perp prices')
        perp_prices = self.client.get_historical_prices(f'{coin}-PERP', resolution, start_timestamp, end_timestamp)
        print('getting future prices')
        future_prices = self.client.get_historical_prices(f'{coin}-0624', resolution, start_timestamp, end_timestamp)

        times = [price['startTime'] for price in perp_prices]
        print(len(perp_prices), len(future_prices))

        dates = mdates.num2date(mdates.datestr2num(times))
        dates = np.array(dates)

        perp_prices = np.array([price['close'] for price in perp_prices])
        future_prices = np.array([price['close'] for price in future_prices])

        print('plotting')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex='col')
        fig.suptitle(coin)

        ax1.plot(dates, perp_prices, linewidth=1)
        ax1.plot(dates, future_prices, linewidth=1)
        ax1.legend(['perp', 'future'])
        ax1.set_ylabel('$')
        ax1.grid()

        ax2.plot(dates, (perp_prices - future_prices) / perp_prices * 100)
        ax2.set_ylabel('%')
        ax2.grid()

        fig.autofmt_xdate()
        plt.show()

    def backtest_carry_expired(self):
        print('start')
        resolution = 14400

        start_timestamp = util.date_to_timestamp_sec(2022, 3, 20, 0)
        end_timestamp = util.date_to_timestamp_sec(2022, 6, 24, 0)

        print('getting perp prices')
        perp_prices = self.client.get_historical_prices(f'{COIN}-PERP', resolution, start_timestamp, end_timestamp)
        print('getting future prices')
        future_prices = self.client.get_historical_prices(f'{COIN}-0624', resolution, start_timestamp,
                                                          end_timestamp)

        times = [price['startTime'] for price in perp_prices]
        print(len(perp_prices), len(future_prices))

        dates = mdates.num2date(mdates.datestr2num(times))
        self.dates = np.array(dates)
        self.perp_prices = np.array([price['close'] for price in perp_prices])
        self.future_prices = np.array([price['close'] for price in future_prices])

        self._backtest()
        self._plot()

    def _backtest(self):
        assert (len(self.dates) == len(self.perp_prices))
        assert (len(self.dates) == len(self.future_prices))

        for i, date in enumerate(self.dates):
            perp_price = self.perp_prices[i]
            future_price = self.future_prices[i]
            self.account.trade(date, perp_price, future_price)

        # self.account.close_trade()
        print(self.account)

    def _plot(self):
        print('plotting')
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 6), sharex='col')
        fig.suptitle(COIN)

        # ax1
        ax1.plot(self.dates, self.perp_prices, linewidth=1)
        ax1.plot(self.dates, self.future_prices, linewidth=1)
        ax1.legend(['perp', 'future'])
        ax1.set_ylabel('$')
        ax1.grid()

        # ax2
        basis = (self.perp_prices - self.future_prices)
        ax2.plot(self.dates, basis, linewidth=1)
        ax2.grid()
        ax2.set_ylabel('$')
        ax2.legend(['basis'])

        # ax3
        basis_perc = basis / self.perp_prices * 100
        ax3.plot(self.dates, basis_perc, linewidth=1)

        # plot trades
        dates = self.account.trades_open.keys()
        trades_open = self.account.trades_open.values()
        ax3.plot(dates, trades_open, 'ro', mfc='none')

        dates = self.account.trades_close.keys()
        trades_close = self.account.trades_close.values()
        ax3.plot(dates, trades_close, 'rx')

        ax3.legend(['basis perc', 'open', 'close'])
        ax3.set_ylabel('%')
        ax3.grid()

        fig.autofmt_xdate()
        plt.show()


if __name__ == '__main__':
    backtester = CarryBacktesting()
    backtester.backtest_carry_expired()
    print('done')
