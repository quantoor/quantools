from datetime import datetime
import matplotlib.pyplot as plt
from FtxClientRest import FtxClient
from dateutil import parser


def main():
    api_key = 'ZTNWpAc4SsCV4nEICM6nwASP4ao7nHYvLSFzXunj'
    api_secret = 'x9tq4yIA27jF83bacZvg-uuFB6Ov6h4n4Ot672QI'
    client = FtxClient(api_key, api_secret)
    start_timestmap = datetime(2021, 9, 1, 0, 0, 0).timestamp()
    end_timestmap = datetime(2021, 10, 1, 0, 0, 0).timestamp()
    fundings_history = client.get_funding_rates(future='MEDIA-PERP')#, start_time=start_timestmap, end_time=end_timestmap)

    times = [parser.parse(i['time']) for i in fundings_history]
    rates = [i['rate'] for i in fundings_history]

    plt.figure()
    plt.plot(times, rates)
    plt.xticks(rotation=45)
    plt.grid()
    plt.show()


if __name__ == '__main__':
    main()
