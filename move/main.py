import pandas as pd
import numpy as np
from common import util
import util as mvutil
import time
import datetime as dt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from tqdm import tqdm
import matplotlib.pyplot as plt
from Volatility import find_vol,Close_to_close

move_symbols = mvutil.get_expired_move_symbols()

N_moves_expired = print(len(move_symbols))

def type_move(move_symbols):
    if ('WK' in move_symbols):
        return 'Weekly'
    elif ('Q' in move_symbols):
        return 'Quarterly'
    else:
        return 'Daily'


resolutions_available = [3600,14400,86400]

def get_percentage_closure():
    move_diff = {'Daily': [], 'Weekly': [], 'Quarterly': []}
    for move in tqdm(move_symbols[0:200]):
        resolution_default = 3600
        ts, mv_prices = util.get_historical_prices(move,resolution_default,0,int(time.time()),verbose=False)
        if (len(mv_prices) == 0):
            resolution_default = 14400
            ts, mv_prices = util.get_historical_prices(move,resolution_default, 0, int(time.time()), verbose=False)
        dates = [dt.datetime.fromtimestamp(t) for t in ts]
        type_of_move = type_move(move)
        int_shift = int(len(dates) / 24/(resolution_default/3600)/2)
        if (type_of_move == 'Daily'):
            start_price = mv_prices[int_shift]
        else:
            start_price = mv_prices[0]
        diff = [p - start_price for p in mv_prices]
        diff_percentage = np.around(diff[-1] / start_price * 100,decimals = 0)
        move_diff[type_of_move] += [diff_percentage]
    return move_diff

def get_IV(move):
    resolution_default = 3600
    ts, mv_prices = util.get_historical_prices(move,resolution_default,0,int(time.time()),verbose=False)
    if (len(mv_prices) == 0):
        resolution_default = 14400
        ts, mv_prices = util.get_historical_prices(move,resolution_default, 0, int(time.time()), verbose=False)
    ul_ts, ul_prices = util.get_historical_prices('BTC/USD',resolution_default,ts[0],ts[-1],verbose=False)
    dates = [dt.datetime.fromtimestamp(t) for t in ts]
    contract = util.get_future_stats(move)
    strike = contract['strikePrice']
    expiry = dates[-1]
    Dte = [ expiry - date for date in dates]
    Tte = [ (dte.days + dte.seconds/(24 * 3600))/365 for dte in Dte]
    r = 0
    call_target = [(target + under - strike)/2 for target,under in zip(mv_prices[:-1],ul_prices)]
    zip_all = zip(Tte[:-1],ul_prices,call_target)
    ivs = [find_vol(target,under,strike,T,r) for T,under,target in zip_all]
    return dates[:-1],ivs


def get_RV(days = 7,method = 'close_to_close'):
    time_end = int(time.time())
    string = "2022-01-01"
    time_begin = time.mktime(dt.datetime.strptime(string,"%Y-%m-%d").timetuple())
    ul_ts, ul_prices = util.get_historical_prices('BTC/USD', 3600, time_begin,time_end, verbose=False)

    plt.plot(ul_prices)
    plt.show()

    RV_days = Close_to_close(ul_prices,days = days)
    plt.plot(RV_days)
    plt.show()

move = move_symbols[4]
# dates,IV_move = get_IV(move)
# plt.plot(IV_move)
# plt.show()
#
get_RV(move)


# fix, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 6), sharex='col')
# ax1.plot(dates[:len(ul_prices)], ul_prices)
# ax1.grid()
# ax2.plot(dates, mv_prices)
# ax2.grid()
# ax3.plot(dates[:len(ul_prices)], diff)
# ax3.grid()
# plt.show()

# fig = make_subplots(rows=3, cols=1, shared_xaxes=True)
#
# fig.add_trace(
#     go.Scatter(x=dates[:len(ul_prices)], y=ul_prices),
#     row=1, col=1
# )
#
# fig.add_trace(
#     go.Scatter(x=dates, y=mv_prices),
#     row=2, col=1
# )
#
# fig.add_trace(
#     go.Scatter(x=dates[:len(ul_prices)], y=diff),
#     row=3, col=1
# )
#
# fig.update_yaxes(
#     showline=True,
#     showgrid=True,
#     showticklabels=True,
#     linecolor='rgb(204, 204, 204)',
#     linewidth=2,
#     mirror=True,
#     # spikemode='across+toaxis',
#     # spikesnap='cursor',
# )
#
# fig.update_xaxes(
#     showline=True,
#     showgrid=True,
#     showticklabels=True,
#     linecolor='rgb(204, 204, 204)',
#     linewidth=2,
#     mirror=True,
#     showspikes=True,
#     spikemode='across+toaxis',
#     spikesnap='cursor',
# )

# fig.update_layout(title_text="Side By Side Subplots")
# fig.update_yaxes(
#     showline=True,
#     showgrid=True,
#     showticklabels=True,
#     linecolor='rgb(204, 204, 204)',
#     linewidth=2,
#     mirror=True,
# ),
# fig.update_xaxes(
#     showline=True,
#     showgrid=True,
#     showticklabels=True,
#     linecolor='rgb(204, 204, 204)',
#     linewidth=2,
#     mirror=True,
# ),
# fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False,
#                  showspikes=True, spikemode='across', spikesnap='cursor', showline=False, spikedash='solid')
# fig.update_xaxes(showgrid=False, zeroline=False, rangeslider_visible=False, showticklabels=False,
#                  showspikes=True, spikemode='across', spikesnap='cursor', showline=False, spikedash='solid')
# fig.update_layout(hoverdistance=0)
# fig.show()
