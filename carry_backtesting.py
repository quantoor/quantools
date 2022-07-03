import util
from FtxClientRest import FtxClient
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

api_key = 'ZTNWpAc4SsCV4nEICM6nwASP4ao7nHYvLSFzXunj'
api_secret = 'x9tq4yIA27jF83bacZvg-uuFB6Ov6h4n4Ot672QI'


# class Position:
#     """ The open position is defined by an entry price and a position size.
#         ROE and PNL can be computed given the mark price.
#     """
#     def __init__(self, entry_price=None, size=0):
#         self.entry_price = entry_price
#         self.size = size
#
#     def __str__(self):
#         return f"Entry price: {self.entry_price}, size: {self.size}"
#
#     def update(self, price, size):
#         self.entry_price = (self.entry_price * self.size + price * size) / (self.size + size)
#         self.size += size
#
#     def _get_roe(self, price):
#         return (price - self.entry_price) / self.entry_price * 100 * self.size / abs(self.size)
#
#     def get_pnl(self, price):
#         return price * abs(self.size) * self._get_roe(price) / 100


class CarryBacktesting:
    def __init__(self):
        self.client = FtxClient(api_key, api_secret)
        self.coin = 'AAVE'

        self.dates = np.array([])
        self.perp_prices = np.array([])
        self.future_prices = np.array([])

        self.perp_position = 0.
        self.future_position = 0.

        self.usd_balance = 1000
        self.total_balance = 1000
        self.trade_amount = 100

    def carry(self):
        futures = self.client.get_all_futures()

        for i in futures:
            if i['type'] == 'future' and not i['perpetual']:

                spotSymbol = i['underlying']
                futureSymbol = i['name']

                try:
                    ul_market = self.client.get_single_market(f'{spotSymbol}/USD')
                except:
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
        perp_prices = self.client.get_historical_prices(f'{self.coin}-PERP', resolution, start_timestamp, end_timestamp)
        print('getting future prices')
        future_prices = self.client.get_historical_prices(f'{self.coin}-0624', resolution, start_timestamp, end_timestamp)

        times = [price['startTime'] for price in perp_prices]
        print(len(perp_prices), len(future_prices))

        dates = mdates.num2date(mdates.datestr2num(times))
        self.dates = np.array(dates)
        self.perp_prices = np.array([price['close'] for price in perp_prices])
        self.future_prices = np.array([price['close'] for price in future_prices])

        self._backtest()
        self._plot()

    def _backtest(self):
        # todo flowchart

        assert (len(self.dates) == len(self.perp_prices))
        assert (len(self.dates) == len(self.future_prices))

        for i, date in enumerate(self.dates):
            perp_price = self.perp_prices[i]
            future_price = self.future_prices[i]

            basis = (perp_price - future_price) / perp_price * 100
            if self.perp_position == 0.:
                if basis > 1.:
                    # sell perp, buy future
                    self.usd_balance -= self.trade_amount
                    self.perp_position += -self.trade_amount / perp_price

                elif basis < -1.:
                    # buy perp, sell future
                    pass

    def buy(self, instrument):
        self.usd_balance

    def sell(self, instrument):
        pass

    def _plot(self):
        print('plotting')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex='col')
        fig.suptitle(self.coin)

        ax1.plot(self.dates, self.perp_prices, linewidth=1)
        ax1.plot(self.dates, self.future_prices, linewidth=1)
        ax1.legend(['perp', 'future'])
        ax1.set_ylabel('$')
        ax1.grid()

        ax2.plot(self.dates, (self.perp_prices - self.future_prices) / self.perp_prices * 100)
        ax2.set_ylabel('%')
        ax2.grid()

        fig.autofmt_xdate()
        plt.show()


if __name__ == '__main__':
    backtester = CarryBacktesting()
    backtester.backtest_carry_expired()
    print('done')
