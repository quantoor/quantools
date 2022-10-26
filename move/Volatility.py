import numpy as np
from scipy.stats import norm
N = norm.cdf
import pandas as pd

def bs_call(S, K, T, r, vol):
    d1 = (np.log(S/K) + (r + 0.5*vol**2)*T) / (vol*np.sqrt(T))
    d2 = d1 - vol * np.sqrt(T)
    return S * norm.cdf(d1) - np.exp(-r * T) * K * norm.cdf(d2)

def bs_vega(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    return S * norm.pdf(d1) * np.sqrt(T)

def find_vol(target_value, S, K, T, r, *args):
    MAX_ITERATIONS = 200
    PRECISION = 1.0e-5
    sigma = 0.5
    for _ in range(0, MAX_ITERATIONS):
        price = bs_call(S, K, T, r, sigma)
        vega = bs_vega(S, K, T, r, sigma)
        diff = target_value - price  # our root
        if (abs(diff) < PRECISION):
            return sigma
        try:
            sigma = sigma + diff/vega # f(x) / f'(x)
        except Exception as e:
            pass
    return sigma # value wasn't found, return best guess so far

def Close_to_close(price_data,days = 7):
    window_time = days * 24
    trading_periods = 365
    print(window_time)
    df_price = pd.DataFrame(price_data,columns = ['close'])
    multiplier = 24
    rs = np.log(df_price['close']/df_price['close'].shift(1))
    result = rs.rolling(window=window_time, center=False).std(ddof=1) * np.sqrt(trading_periods * multiplier)
    return result