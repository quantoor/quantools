import util
from FtxClientRest import FtxClient
from dateutil import parser
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

api_key = 'ZTNWpAc4SsCV4nEICM6nwASP4ao7nHYvLSFzXunj'
api_secret = 'x9tq4yIA27jF83bacZvg-uuFB6Ov6h4n4Ot672QI'
client = FtxClient(api_key, api_secret, 'Funding')


def historic_funding_rates():
    start_timestmap = util.date_to_timestamp_sec(2021, 6, 1, 0)
    end_timestmap = util.date_to_timestamp_sec(2021, 6, 29, 0)
    fundings_history = client.get_funding_rates(future='MEDIA-PERP', start_time=start_timestmap, end_time=end_timestmap)

    times = [parser.parse(i['time']) for i in fundings_history]
    rates = [i['rate'] for i in fundings_history]

    plt.figure()
    plt.plot(times, rates)
    plt.xticks(rotation=45)
    plt.grid()
    plt.show()


def search_funding_rates():
    fr = client.get_all_funding_rates()


def analyze_funding_payments():
    start_timestamp = util.date_to_timestamp_sec(2022, 6, 29, 0)
    end_timestamp = util.timestamp_now()
    funding_payments = client.get_funding_payments(start_timestamp, end_timestamp)

    instrument_payments = {}  # instrument: tot_payment
    for fp in funding_payments:

        name = fp['future']

        if name in instrument_payments:
            instrument_payments[name] += fp['payment']
        else:
            instrument_payments[name] = 0

    return instrument_payments


def carry():
    futures = client.get_all_futures()

    for i in futures:
        if i['type'] == 'future' and not i['perpetual']:

            spotSymbol = i['underlying']
            futureSymbol = i['name']

            try:
                ul_market = client.get_single_market(f'{spotSymbol}/USD')
            except:
                continue
            ul_price = ul_market['price']
            future_price = i['mark']

            # higher = max(ul_price, futurePrice)
            # lower = min(ul_price, futurePrice)
            basis = (future_price - ul_price) / ul_price * 100

            if abs(basis) > 3:
                print(f'{spotSymbol}: spot {ul_price}, {futureSymbol} {future_price}, basis {round(basis, 1)} %')


def analyze_carry():
    coins = {}  # {'coin': [a,b,c]}

    markets = client.get_markets()
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

    coins = {key: value for (key, value) in coins.items() if len(value) > 2 and key == '1INCH'}

    start_timestamp = util.date_to_timestamp_sec(2022, 1, 1, 0)
    end_timestamp = util.timestamp_now()

    for coin in coins:
        spot_prices = client.get_historical_prices(f'{coin}/USD', 3600, start_timestamp, end_timestamp)
        perp_prices = client.get_historical_prices(f'{coin}-PERP', 3600, start_timestamp, end_timestamp)
        future_prices = client.get_historical_prices(f'{coin}-0930', 3600, start_timestamp, end_timestamp)

        # print(spot_prices[0]['time'], perp_prices[0]['time'], future_prices[0]['time'])
        # print(spot_prices[-1]['time'], perp_prices[-1]['time'], future_prices[-1]['time'])

        times = [price['startTime'] for price in spot_prices]
        dates = mdates.num2date(mdates.datestr2num(times))
        dates = np.array(dates)

        spot_prices = np.array([price['close'] for price in spot_prices])
        perp_prices = np.array([price['close'] for price in perp_prices])
        future_prices = np.array([price['close'] for price in future_prices])

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
        # fig.show()

    plt.show()


def analyze_carry_expired():
    print('start')

    coin = '1INCH'
    resolution = 14400
    # expired_futures = client.get_expired_futures()
    # expired_futures_btc = [i for i in expired_futures if i['underlying'] == coin and i['type'] == 'future']

    start_timestamp = util.date_to_timestamp_sec(2022, 3, 20, 0)
    end_timestamp = util.date_to_timestamp_sec(2022, 6, 24, 0)

    print('getting perp prices')
    perp_prices = client.get_historical_prices(f'{coin}-PERP', resolution, start_timestamp, end_timestamp)
    print('getting future prices')
    future_prices = client.get_historical_prices(f'{coin}-0624', resolution, start_timestamp, end_timestamp)
    # funding_rate = client.get_funding_rates(f'{coin}-PERP', start_timestamp, end_timestamp)  # todo plot funding rate

    times = [price['startTime'] for price in perp_prices]
    print(len(perp_prices), len(future_prices))

    dates = mdates.num2date(mdates.datestr2num(times))
    dates = np.array(dates)

    perp_prices = np.array([price['close'] for price in perp_prices])
    future_prices = np.array([price['close'] for price in future_prices])
    # todo trim perp to same length of futures

    print('plotting')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex='col')
    fig.suptitle(coin)

    # ax.plot(dates, spot_prices)
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


# historic_funding_rates()
# pt = analyze_funding_payments()
# carry()
# analyze_carry()
analyze_carry_expired()
print('done')
