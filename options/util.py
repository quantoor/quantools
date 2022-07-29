import time
import datetime as dt
from scipy.interpolate import interp1d
import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm
from math import sqrt, pi


def N(z):
    """ Normal cumulative density function
    :param z: point at which cumulative density is calculated
    :return: cumulative density under normal curve
    """
    return norm.cdf(z)


def black_scholes_call_value(S, K, r, t, vol):
    """ Black-Scholes call option
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param vol: volatility
    :return: BS call option value
    """
    d1 = (1.0 / (vol * np.sqrt(t))) * (np.log(S / K) + (r + 0.5 * vol ** 2.0) * t)
    d2 = d1 - (vol * np.sqrt(t))
    return N(d1) * S - N(d2) * K * np.exp(-r * t)


def black_scholes_put_value(S, K, r, t, vol):
    """ Black-Scholes put option
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param vol: volatility
    :return: BS put option value
    """
    d1 = (1.0 / (vol * np.sqrt(t))) * (np.log(S / K) + (r + 0.5 * vol ** 2.0) * t)
    d2 = d1 - (vol * np.sqrt(t))
    return N(-d2) * K * np.exp(-r * t) - N(-d1) * S


# helper function phi
def phi(x):
    """ Phi helper function
    """
    return np.exp(-0.5 * x * x) / (sqrt(2.0 * pi))


# shared
def gamma(S, K, r, t, vol):
    """ Black-Scholes gamma
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param vol: volatility
    :return: gamma
    """
    d1 = (1.0 / (vol * np.sqrt(t))) * (np.log(S / K) + (r + 0.5 * vol ** 2.0) * t)
    return phi(d1) / (S * vol * sqrt(t))


def vega(S, K, r, t, vol):
    """ Black-Scholes vega
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param vol: volatility
    :return: vega
    """
    d1 = (1.0 / (vol * np.sqrt(t))) * (np.log(S / K) + (r + 0.5 * vol ** 2.0) * t)
    return (S * phi(d1) * sqrt(t)) / 100.0


# call options
def call_delta(S, K, r, t, vol):
    """ Black-Scholes call delta
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param vol: volatility
    :return: call delta
    """
    d1 = (1.0 / (vol * np.sqrt(t))) * (np.log(S / K) + (r + 0.5 * vol ** 2.0) * t)
    return N(d1)


def call_theta(S, K, r, t, vol):
    """ Black-Scholes call theta
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param vol: volatility
    :return: call theta
    """
    d1 = (1.0 / (vol * np.sqrt(t))) * (np.log(S / K) + (r + 0.5 * vol ** 2.0) * t)
    d2 = d1 - (vol * np.sqrt(t))
    theta = -((S * phi(d1) * vol) / (2.0 * np.sqrt(t))) - (
            r * K * np.exp(-r * t) * N(d2)
    )
    return theta / 365.0


def call_rho(S, K, r, t, vol):
    """ Black-Scholes call rho
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param vol: volatility
    :return: call rho
    """
    d1 = (1.0 / (vol * np.sqrt(t))) * (np.log(S / K) + (r + 0.5 * vol ** 2.0) * t)
    d2 = d1 - (vol * np.sqrt(t))
    rho = K * t * np.exp(-r * t) * N(d2)
    return rho / 100.0


# put options
def put_delta(S, K, r, t, vol):
    """ Black-Scholes put delta
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param vol: volatility
    :return: put delta
    """
    d1 = (1.0 / (vol * np.sqrt(t))) * (np.log(S / K) + (r + 0.5 * vol ** 2.0) * t)
    return N(d1) - 1.0


def put_theta(S, K, r, t, vol):
    """ Black-Scholes put theta
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param vol: volatility
    :return: put theta
    """
    d1 = (1.0 / (vol * np.sqrt(t))) * (np.log(S / K) + (r + 0.5 * vol ** 2.0) * t)
    d2 = d1 - (vol * np.sqrt(t))
    theta = -((S * phi(d1) * vol) / (2.0 * np.sqrt(t))) + (
            r * K * np.exp(-r * t) * N(-d2)
    )
    return theta / 365.0


def put_rho(S, K, r, t, vol):
    """ Black-Scholes put rho
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param vol: volatility
    :return: put rho
    """
    d1 = (1.0 / (vol * np.sqrt(t))) * (np.log(S / K) + (r + 0.5 * vol ** 2.0) * t)
    d2 = d1 - (vol * np.sqrt(t))
    rho = -K * t * np.exp(-r * t) * N(-d2)
    return rho / 100.0


def call_implied_volatility_objective_function(S, K, r, t, vol, call_option_market_price):
    """ Objective function which sets market and model prices to zero
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param vol: volatility
    :param call_option_market_price: market observed option price
    :return: error between market and model price
    """
    return call_option_market_price - black_scholes_call_value(S, K, r, t, vol)


def call_implied_volatility(S, K, r, t, call_option_market_price, a=-2.0, b=2.0, xtol=1e-6):
    """ Call implied volatility function
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param call_option_market_price: market observed option price
    :param a: lower bound for brentq method
    :param b: upper gound for brentq method
    :param xtol: tolerance which is considered good enough
    :return: volatility to sets the difference between market and model price to zero
    """
    # avoid mirroring outer scope
    _S, _K, _r, _t, _call_option_market_price = S, K, r, t, call_option_market_price

    # define a nested function that takes our target param as the input

    def fcn(vol):
        # returns the difference between market and model price at given volatility
        return call_implied_volatility_objective_function(_S, _K, _r, _t, vol, _call_option_market_price)

    # first we try to return the results from the brentq algorithm
    try:
        result = brentq(fcn, a=a, b=b, xtol=xtol)
        # if the results are *too* small, sent to np.nan so we can later interpolate
        return np.nan if result <= 1.0e-6 else result
    # if it fails then we return np.nan so we can later interpolate the results
    except ValueError:
        return np.nan


def put_implied_volatility_objective_function(S, K, r, t, vol, put_option_market_price):
    """ Objective function which sets market and model prices to zero
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param vol: volatility
    :param put_option_market_price: market observed option price
    :return: error between market and model price
    """
    return put_option_market_price - black_scholes_put_value(S, K, r, t, vol)


def put_implied_volatility(S, K, r, t, put_option_market_price, a=-2.0, b=2.0, xtol=1e-6):
    """ Put implied volatility function
    :param S: underlying
    :param K: strike price
    :param r: rate
    :param t: time to expiration
    :param put_option_market_price: market observed option price
    :param a: lower bound for brentq method
    :param b: upper gound for brentq method
    :param xtol: tolerance which is considered good enough
    :return: volatility to sets the difference between market and model price to zero
    """
    # avoid mirroring out scope
    _S, _K, _r, _t, _put_option_market_price = S, K, r, t, put_option_market_price

    # define a nsted function that takes our target param as the input
    def fcn(vol):
        # returns the difference between market and model price at given volatility
        return put_implied_volatility_objective_function(
            _S, _K, _r, _t, vol, _put_option_market_price
        )

    # first we try to return the results from the brentq algorithm
    try:
        result = brentq(fcn, a=a, b=b, xtol=xtol)
        # if the results are *too* small, sent to np.nan so we can later interpolate
        return np.nan if result <= 1.0e-6 else result
    # if it fails then we return np.nan so we can later interpolate the results
    except ValueError:
        return np.nan


def get_days_until_expiration(series):
    """ Return the number of days until expiration
    :param series: row of the dataframe, accessible by label
    :return: days until expiration
    """
    expiration = series["Expiration"]
    # add the hours to the expiration date so we get the math correct
    date_str = expiration.strftime("%Y-%m-%d") + " 23:59:59"
    # convert date string into datetime object
    expiry = dt.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    # get today
    # since we need to use a cached data source, revert to that date
    # today = dt.datetime.today()
    today = dt.datetime(2016, 1, 18)
    # return the difference and add one to count for today
    return (expiry - today).days + 1


def get_time_fraction_until_expiration(series):
    """ Return the fraction of a year until expiration
      You don't always have to be this precise. The difference in price
      based on a few hours for long dated options or far OTM options
      will not be affected. However for liquid, ATM options with short
      expiration windows, every second counts!
      :param series: row of the dataframe, accessible by label
      :return: fraction of a year until expiration
      """
    expiration = series["Expiration"]
    # add the hours to the expiration date so we get the math correct
    date_str = expiration.strftime("%Y-%m-%d") + " 23:59:59"
    # convert date string into datetime object
    time_tuple = time.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    # get the number of seconds from the epoch until expiration
    expiry_in_seconds_from_epoch = time.mktime(time_tuple)
    # get the number of seconds from the epoch to right now
    # since we need to use a cached data source, revert to that date
    # today = dt.datetime.today()
    # right_now_in_seconds_from_epoch = time.time()
    right_now_in_seconds_from_epoch = dt.datetime(2016, 1, 18).timestamp()
    # get the total number of seconds to expiration
    seconds_until_expiration = (
            expiry_in_seconds_from_epoch - right_now_in_seconds_from_epoch
    )
    # seconds in year
    seconds_in_year = 31536000.0
    # fraction of seconds to expiration to total in year, rounded
    return max(seconds_until_expiration / seconds_in_year, 1e-10)


# define terms and associated rates, these should coincide with our options
# these rates are taken from the yield curve
terms = [30, 3 * 30, 6 * 30, 12 * 30, 24 * 30, 36 * 30, 60 * 30]
rates = [0.0001, 0.0009, 0.0032, 0.0067, 0.0097, 0.0144, 0.0184]


def get_rate(series):
    """ Interpolate rates out to 30 years
    Note computing rates like this is not strictly theoretically
    correct but works for illustrative purposes
    :param series: row of the dataframe, accessable by label
    :return interpolated interest rate based on term structure
    """
    days = series["DaysUntilExpiration"]
    # generate terms for every thirty days up until our longest expiration
    new_terms = [i for i in range(30, (60 * 30) + 1)]
    # create linear interpolation model
    f = interp1d(terms, rates, kind="linear")
    # interpolate the values based on the new terms we created above
    ff = f(new_terms)
    # return the interpolated rate given the days to expiration
    return round(ff[max(days, 30) - 30], 8)


def get_mid(series):
    """ Get the mid price between bid and ask
    :param series: row of the dataframe, accessable by label
    :return mid price
    """
    bid = series["Bid"]
    ask = series["Ask"]
    last = series["Last"]
    # if the bid or ask doesn't exist, return 0.0
    if np.isnan(ask) or np.isnan(bid):
        return 0.0
    # if the bid or ask are 0.0, return the last traded price
    elif ask == 0.0 or bid == 0.0:
        return last
    else:
        return (ask + bid) / 2.0


def get_implied_vol_mid(series):
    """
    """
    option_type = series["OptionType"]
    S = series["UnderlyingPrice"]
    K = series["Strike"]
    r = series["InterestRate"]
    t = series["TimeUntilExpiration"]
    mid = series["Mid"]

    # build method name
    meth_name = "{0}_implied_volatility".format(option_type)
    # call from globals()
    return float(globals().get(meth_name)(S, K, r, t, mid))


def interp_implied_volatility(options_frame):
    """ Interpolate missing (np.nan) values of implied volatility
    We first need to split the chains into expiration and type because we cannot
    interpolate across the entire chain, rather within these two groups
    :param options_frame: DataFrame containing options data
    :return original DataFrame with ImpliedVolatilityMid column containing interpolated values
    """
    # create a MultiIndex with Expiration, OptionType, the Strike as index, then sort
    frame = options_frame.set_index(["Expiration", "OptionType", "Strike"]).sort_index()
    # pivot the frame with ImpliedVolatilityMid as the values within the table
    # this has Strikes along the rows and Expirations along the columns
    # the level=1 unstack pivots on Expiration and level=0 unstack pivots on OptionType
    unstacked = frame["ImpliedVolatilityMid"].unstack(level=1).unstack(level=0)
    # this line does three things:
    # first interpolates across each Expiration date down the strikes for np.nan values
    # second forward fills values which keeps the last interpolated value as the value to fill
    # third back fills values which keeps the first interpolated value as the value to fill
    unstacked_interp = unstacked.interpolate().ffill().bfill()
    # restack into shape of original DataFrame
    unstacked_interp_indexed = (unstacked_interp.stack(level=0).stack(level=0).reset_index())
    # replace old column with the new column with interpolated and filled values
    frame["ImpliedVolatilityMid"] = unstacked_interp_indexed.set_index(["Expiration", "OptionType", "Strike"])
    # give our index back
    frame.reset_index(inplace=True)
    return frame


def get_option_value(series):
    """ Return the option value given the OptionType
    :param series: row of the dataframe, accessible by label
    :return: Black-Scholes option value
    """
    option_type = series["OptionType"]
    S = series["UnderlyingPrice"]
    K = series["Strike"]
    r = series["InterestRate"]
    t = series["TimeUntilExpiration"]
    vol = series["ImpliedVolatilityMid"]
    meth_name = "black_scholes_{0}_value".format(option_type)
    return float(globals().get(meth_name)(S, K, r, t, vol))


def get_delta(series):
    """ Return the option delta given the OptionType
    :param series: row of the dataframe, accessible by label
    :return: option delta
    """
    option_type = series["OptionType"]
    S = series["UnderlyingPrice"]
    K = series["Strike"]
    r = series["InterestRate"]
    t = series["TimeUntilExpiration"]
    vol = series["ImpliedVolatilityMid"]
    meth_name = "{0}_delta".format(option_type)
    return float(globals().get(meth_name)(S, K, r, t, vol))


def get_gamma(series):
    """ Return the option gamma
    :param series: row of the dataframe, accessible by label
    :return: option gamma
    """
    S = series["UnderlyingPrice"]
    K = series["Strike"]
    r = series["InterestRate"]
    t = series["TimeUntilExpiration"]
    vol = series["ImpliedVolatilityMid"]
    return float(gamma(S, K, r, t, vol))


def get_vega(series):
    """ Return the option vega
    :param series: row of the dataframe, accessible by label
    :return: option vega
    """
    S = series["UnderlyingPrice"]
    K = series["Strike"]
    r = series["InterestRate"]
    t = series["TimeUntilExpiration"]
    vol = series["ImpliedVolatilityMid"]
    return float(vega(S, K, r, t, vol))


def get_theta(series):
    """ Return the option theta given the OptionType
    :param series: row of the dataframe, accessible by label
    :return: option theta
    """
    option_type = series["OptionType"]
    S = series["UnderlyingPrice"]
    K = series["Strike"]
    r = series["InterestRate"]
    t = series["TimeUntilExpiration"]
    vol = series["ImpliedVolatilityMid"]
    meth_name = "{0}_theta".format(option_type)
    return float(globals().get(meth_name)(S, K, r, t, vol))


def get_rho(series):
    """ Return the option rho given the OptionType
    :param series: row of the dataframe, accessible by label
    :return: option rho
    """
    option_type = series["OptionType"]
    S = series["UnderlyingPrice"]
    K = series["Strike"]
    r = series["InterestRate"]
    t = series["TimeUntilExpiration"]
    vol = series["ImpliedVolatilityMid"]
    meth_name = "{0}_rho".format(option_type)
    return float(globals().get(meth_name)(S, K, r, t, vol))


def get_model_error(series):
    """ Return the error between mid price and model price
    :param series: row of the dataframe, accessible by label
    :return: error between mid price and model price
    """
    option_mid = series["Mid"]
    return option_mid - get_option_value(series)
