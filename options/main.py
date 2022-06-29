import pandas as pd
import matplotlib as mat

# mat.style.use("ggplot")
import matplotlib.pyplot as plt

# for plotting the vol surface
from mpl_toolkits.mplot3d import Axes3D
import scipy

from util import *

print(f"Numpy {np.__version__}\nMatplotlib {mat.__version__}\nScipy {scipy.__version__}\nPandas {pd.__version__}")

# underlying stock price
S = 45.0
# series of underlying stock prices to demonstrate a payoff profile
S_ = np.arange(35.0, 55.0, 0.01)
# strike price
K = 45.0
# time to expiration (you'll see this as T-t in the equation)
t = 164.0 / 365.0
# risk free rate (there's nuance to this which we'll describe later)
r = 0.02
# volatility (latent variable which is the topic of this talk)
vol = 0.25
# black scholes prices for demonstrating trades
atm_call_premium = 3.20
atm_put_premium = 2.79
otm_call_premium = 1.39
otm_put_premium = 0.92

call_payoff = lambda S, K: np.maximum(S - K, 0)
put_payoff = lambda S, K: np.maximum(K - S, 0)

# plot the call payoff
# plt.figure(1, figsize=(7, 4))
# plt.title("Call option payoff at expiration")
# plt.xlabel("Underlying stock price, S")
# plt.axhline(y=0, lw=1, c="grey")
# plt.plot(S_, -atm_call_premium + call_payoff(S_, K))
# plt.show()

# plot the put payoff
# plt.figure(2, figsize=(7, 4))
# plt.title("Put option payoff at expiration")
# plt.xlabel("Underlying stock price, S")
# plt.axhline(y=0, lw=1, c="grey")
# plt.plot(S_, -atm_put_premium + put_payoff(S_, K))
# plt.show()

# plot a long straddle payoff
long_straddle_premium = atm_call_premium + atm_put_premium
long_straddle_payoff = lambda S, K: call_payoff(S, K) + put_payoff(S, K)

# plt.figure(2, figsize=(7, 4))
# plt.title("Long straddle payoff at expiration")
# plt.xlabel("Underlying stock price, S")
# plt.axhline(y=0, lw=1, c="grey")
# plt.plot(S_, -long_straddle_premium + long_straddle_payoff(S_, K))
# plt.show()

# plot a short straddle payoff
# plt.figure(2, figsize=(7, 4))
# plt.title("Short straddle payoff at expiration")
# plt.xlabel("Underlying stock price, S")
# plt.axhline(y=0, lw=1, c="grey")
# plt.plot(S_, long_straddle_premium - long_straddle_payoff(S_, K))

# plot a short iron condor payoff
short_iron_condor = (
        call_payoff(S_, K + 5)  # long otm call
        - call_payoff(S_, K)  # short atm call
        - put_payoff(S_, K)  # short atm put
        + put_payoff(S_, K - 5)  # long atm put
)

short_iron_condor_premium = (-otm_call_premium + atm_call_premium + atm_put_premium - otm_put_premium)

# plt.figure(5, figsize=(7, 4))
# plt.title("Short iron condor payoff at expiration")
# plt.xlabel("Underlying stock price, S")
# plt.axhline(y=0, lw=1, c="grey")
# plt.plot(S_, short_iron_condor_premium + short_iron_condor)

# black scholes
call_value = black_scholes_call_value(S, K, r, t, vol)
put_value = black_scholes_put_value(S, K, r, t, vol)
print(f"Black-Scholes call value {call_value:.2f}")
print(f"Black-Scholes put value {put_value:.2f}")

# get the value of the option with six months to expiration
black_scholes_call_value_six_months = (black_scholes_call_value(S_, K, r, 0.5, vol) - atm_call_premium)
# get the value of the option with three months to expiration
black_scholes_call_value_three_months = (black_scholes_call_value(S_, K, r, 0.25, vol) - atm_call_premium)
# get the value of the option with one month to expiration
black_scholes_call_value_one_month = (black_scholes_call_value(S_, K, r, 1.0 / 12.0, vol) - atm_call_premium)
# get payoff value at expiration
call_payoff_at_expiration = call_payoff(S_, K) - atm_call_premium

# plot the call payoffs
# plt.figure(3, figsize=(7, 4))
# plt.plot(S_, black_scholes_call_value_six_months)
# plt.plot(S_, black_scholes_call_value_three_months)
# plt.plot(S_, black_scholes_call_value_one_month)
# plt.plot(S_, call_payoff_at_expiration)
# plt.axhline(y=0, lw=1, c="grey")
# plt.title("Black-Scholes price of option through time")
# plt.xlabel("Underlying stock price, S")
# plt.legend(["t=0.5", "t=0.25", "t=0.083", "t=0"], loc=2)
# plt.show()

# real options market data
underlying_symbol = "IBM"
options_frame = pd.read_pickle("./options_frame.pickle")

# reset the index so the strike and expiration become columns
options_frame.reset_index(inplace=True)

# rename the columns for consistency
columns = {
    "Expiry": "Expiration",
    "Type": "OptionType",
    "Symbol": "OptionSymbol",
    "Vol": "Volume",
    "Open_Int": "OpenInterest",
    "Underlying_Price": "UnderlyingPrice",
    "Quote_Time": "QuoteDatetime",
    "Underlying": "UnderlyingSymbol",
    "Chg": "OptionChange",
}
options_frame.rename(columns=columns, inplace=True)

# use the apply method to pass each row as a series to the various methods, returns a series in this case
options_frame["DaysUntilExpiration"] = options_frame.apply(get_days_until_expiration, axis=1)
options_frame["TimeUntilExpiration"] = options_frame.apply(get_time_fraction_until_expiration, axis=1)
options_frame["InterestRate"] = options_frame.apply(get_rate, axis=1)
options_frame["Mid"] = options_frame.apply(get_mid, axis=1)

# apply the function to the dataframe rowwise
options_frame["ImpliedVolatilityMid"] = options_frame.apply(get_implied_vol_mid, axis=1)

# print(options_frame.info())

bad_iv = options_frame[np.isnan(options_frame["ImpliedVolatilityMid"])]

# map the count function to each strike where there is a nan implied volatility
print(bad_iv.groupby(["Strike"]).count()["Expiration"])

# get the completed frame
options_frame = interp_implied_volatility(options_frame)

# check to see if there are any np.nans
bad_iv_post = options_frame[np.isnan(options_frame["ImpliedVolatilityMid"])]

print(bad_iv_post.groupby(["Strike"]).count()["Expiration"])

# use the apply method to pass each row as a series to the various methods, returns a series in this case
options_frame["TheoreticalValue"] = options_frame.apply(get_option_value, axis=1)
options_frame["Delta"] = options_frame.apply(get_delta, axis=1)
options_frame["Gamma"] = options_frame.apply(get_gamma, axis=1)
options_frame["Vega"] = options_frame.apply(get_vega, axis=1)
options_frame["Theta"] = options_frame.apply(get_theta, axis=1)
options_frame["Rho"] = options_frame.apply(get_rho, axis=1)
options_frame["ModelError"] = options_frame.apply(get_model_error, axis=1)

# print each of the results
print("Black-Scholes call delta %0.4f" % call_delta(S, K, r, t, vol))
print("Black-Scholes put delta %0.4f" % put_delta(S, K, r, t, vol))
print("Black-Scholes gamma %0.4f" % gamma(S, K, r, t, vol))
print("Black-Scholes vega %0.4f" % vega(S, K, r, t, vol))
print("Black-Scholes call theta %0.4f" % call_theta(S, K, r, t, vol))
print("Black-Scholes put theta %0.4f" % put_theta(S, K, r, t, vol))
print("Black-Scholes call rho %0.4f" % call_rho(S, K, r, t, vol))
print("Black-Scholes put rho %0.4f" % put_rho(S, K, r, t, vol))

# plot the model error
options_frame["ModelError"].hist(figsize=(7, 4))
plt.show()
