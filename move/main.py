import pandas as pd
import numpy as np
import common.util as util
import move.util as mvutil
import time
import datetime as dt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from tqdm import tqdm
import matplotlib.pyplot as plt
from move.Volatility import find_vol,Close_to_close
from move.Greeks import OptionPricing

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
    put_target = [(target + strike - under)/2 for target,under in zip(mv_prices[:-1],ul_prices)]

    # plt.plot(put_target,label ='put_target')
    # plt.plot(mv_prices,label = 'mv_prices')
    # plt.legend(loc ='upper right')
    # plt.show()

    zip_all = zip(Tte[:-1],ul_prices,put_target)
    ivs = []
    for T,under,target in zip_all:
        try:
            iv = find_vol(target,strike,under,T,r)
        except Exception as e:
            iv = np.NaN
        ivs.append(iv)
    ivs.append(ivs[-1])
    return dates[:-1],ivs,mv_prices

def Greeks_PNL(move):
    resolution_default = 3600
    ts, mv_prices = util.get_historical_prices(move,resolution_default,0,int(time.time()),verbose=False)
    if (len(mv_prices) == 0):
        resolution_default = 14400
        ts, mv_prices = util.get_historical_prices(move,resolution_default, 0, int(time.time()), verbose=False)
    ul_ts, ul_prices = util.get_historical_prices('BTC/USD',resolution_default,ts[0],ts[-1] + resolution_default,verbose=False)
    dates = [dt.datetime.fromtimestamp(t) for t in ts]
    contract = util.get_future_stats(move)
    print(contract)
    expiration_price = contract['expirationPrice']
    strike = contract['strikePrice']
    expiry = dates[-1]
    Dte = [ expiry - date for date in dates]
    Tte = [ (dte.days + dte.seconds/(24 * 3600))/365 for dte in Dte]
    _,ivs,_ = get_IV(move)
    print(f'strike = {strike}')
    dS = np.diff(ul_prices)
    dT = resolution_default/(3600 * 24)

    delta_pnl = 0
    gamma_pnl = 0
    vega_pnl = 0
    theta_pnl = 0

    total_delta_pnl = [0]
    total_gamma_pnl = [0]
    total_vega_pnl = [0]
    total_theta_pnl = [0]

    N_mv = len(mv_prices)
    N_iv = len(ivs)
    print('number of move prices =', N_mv)
    print('number of iv prices = ', N_iv)
    option_c = OptionPricing('c',ul_prices[0],strike,Tte[0],ivs[0],r = 0, slope = 0)
    option_p = OptionPricing('p',ul_prices[0],strike,Tte[0],ivs[0],r = 0, slope = 0)
    delta = option_c.Delta() + option_p.Delta()
    gamma = option_c.Gamma() + option_p.Gamma()
    vega = option_c.Vega() + option_p.Vega()
    theta = option_c.Theta() + option_p.Theta()

    for i in range(1,N_mv):

        delta_pnl = delta * dS[i-1]
        gamma_pnl = 0.5 * gamma * dS[i-1]**2
        theta_pnl = theta * dT

        if np.isnan(ivs[i]):
            vega_pnl = 0
            delta = 0
            vega = 0
            theta = 0
            gamma = 0
        else:
            if np.isnan(ivs[i-1]):
                vega_pnl = 0
            else:
                dIV = ivs[i] - ivs[i-1]
                vega_pnl = vega * dIV * 100

            option_c = OptionPricing('c', ul_prices[i],strike,Tte[i],ivs[i],r=0,slope=0)
            option_p = OptionPricing('p', ul_prices[i],strike,Tte[i],ivs[i],r=0,slope=0)
            delta = option_c.Delta() + option_p.Delta()
            gamma = option_c.Gamma() + option_p.Gamma()
            vega = option_c.Vega() + option_p.Vega()
            theta = option_c.Theta() + option_p.Theta()

        total_delta_pnl.append(total_delta_pnl[-1] + delta_pnl)
        total_vega_pnl.append(total_vega_pnl[-1] + vega_pnl)
        total_gamma_pnl.append(total_gamma_pnl[-1] + gamma_pnl)
        total_theta_pnl.append(total_theta_pnl[-1] + theta_pnl)

    add_ivs_missing = []
    pnl_rebuilt = mv_prices[0] + np.array(total_theta_pnl) + np.array(total_vega_pnl) + np.array(total_delta_pnl) + np.array(total_gamma_pnl)

    for i in range(N_iv):
        if (np.isnan(ivs[i])):
            add_ivs_missing.append(mv_prices[i])
        else:
            add_ivs_missing.append(pnl_rebuilt[i])
    add_ivs_missing = np.array(add_ivs_missing)

    plt.plot(add_ivs_missing)
    plt.show()

    fig, axs = plt.subplots(2, 2, figsize=(10,10))
    axs[0, 0].plot(total_delta_pnl)
    axs[0, 0].set_title('Delta PNL')
    #
    axs[0, 1].plot(total_gamma_pnl)
    axs[0, 1].set_title('Gamma PNL')
    # plt.show()
    axs[1,0].plot(total_vega_pnl)
    axs[1,0].set_title('Vega PNL')

    axs[1,1].plot(total_theta_pnl)
    axs[1,1].set_title('Theta PNL')

    plt.show()
    fig, axs = plt.subplots(2, 2, figsize=(10, 10))
    axs[0,0].plot(add_ivs_missing,label ='greeks')
    axs[0,0].plot(mv_prices,label = 'real')
    axs[0,0].legend(loc = 'upper right')
    axs[0,0].set_title('Real price and price from greeks')

    axs[0,1].plot(ul_prices)
    axs[0,1].set_title('Underlying price')

    axs[1,0].scatter(Tte[::-1],ivs)
    axs[1,0].set_title('Implied volatility')

    axs[1,1].plot(dS)
    axs[1,1].set_title('Diff Underlying')
    plt.show()

    print(expiration_price)
    print(np.abs(strike - ul_prices[-1]))

    # plt.plot(theoric_prices,label = 'theoric')
    # plt.plot(mv_prices,label = 'mv_prices')
    # plt.legend(loc = 'upper right')
    # plt.show()

def get_RV(lookback,days = 7,method = 'close_to_close'):
    time_end = int(time.time())
    time_begin = time.mktime(dt.datetime.strptime(lookback,"%Y-%m-%d").timetuple())
    ul_ts, ul_prices = util.get_historical_prices('BTC/USD', 3600, time_begin,time_end, verbose=False)
    dates = [dt.datetime.fromtimestamp(t) for t in ul_ts]
    print(dates[0],dates[-1])
    RV_days = Close_to_close(ul_prices,days = days)
    return dates,RV_days

def Risk_vol_premium(move,lookback,days = 7):
    dates_IV,IVs,mv_prices = get_IV(move)
    dates_RV,RVs = get_RV(lookback,days)

    IV_series = dict(zip(dates_IV,IVs))
    RV_series = dict(zip(dates_RV,RVs))
    common_dates = list(set(IV_series) & set(RV_series))

    RVP = { t : IV_series[t] - RV_series[t] for t in common_dates}

    plt.scatter(RVP.keys(),RVP.values())
    plt.show()

    # plt.plot(mv_prices)
    # plt.show()

    # plt.plot(IV_series.keys(),IV_series.values())
    # plt.show()
    return RVP

def main(move):
    print(f'move is {move}')
    Greeks_PNL(move)

# Risk_vol_premium(move)
# plt.plot(IV_move)
# plt.show()
#
# lookback = '2022-01-01'
# _,RV = get_RV(lookback,days = 7)
# plt.plot(RV)
# plt.show()
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