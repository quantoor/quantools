# coding=utf-8

import ccxt

ftx = ccxt.ftx()

markets = ftx.load_markets()
for i in markets.values():
    if not i['spot']:
        fr = ftx.fetchFundingRate(i['symbol'])
        if fr['fundingRate'] is not None and fr['fundingRate'] > 1e-4:
            print(i['symbol'], fr['fundingRate'] * 100, '%')

print('done')
