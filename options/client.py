import ccxt

client = ccxt.deribit()
# a = client.fetch_markets()
# b = client.fetch_ticker('SOL/USD:SOL-220731-48-C')
tickers = client.fetch_tickers()
# d = client.fetch_ohlcv('BTC/USD:BTC-221230-19000-P', timeframe='1h', limit=50)
# e = client.fetch_order_book('BTC/USD:BTC-221230-19000-P', limit=5)
# f = client.fetch_historical_volatility('BTC')

# id = 'SOL-31JUL22-48-C'
# symbol = 'SOL/USD:SOL-220731-48-C'


import black_scholes as bs

pars = [23816, 23000, 0, 6. / 365., 0.7]
call_price = bs.call_price(*pars)
print(call_price)
# put = bs_put_price(23932, 23000, 0, 6./365., 0.7)
# print(put)
print(f'delta: {bs.call_delta(*pars)}')
print(f'gamma: {bs.gamma(*pars)}')
print(f'vega: {bs.vega(*pars)}')
print(f'theta: {bs.call_theta(*pars)}')
print(f'call iv {bs.call_iv(*pars, call_price)}')
