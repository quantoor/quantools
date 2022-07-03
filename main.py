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


# historic_funding_rates()
# pt = analyze_funding_payments()
print('done')
