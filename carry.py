# coding=utf-8

import ccxt

ftx = ccxt.ftx()

markets = ftx.load_markets()

for i in markets.values():
    if i['future']:

        base = i['base']
        quote = i['quote']
        spotSymbol = f'{base}/{quote}:{quote}'
        futureSymbol = i['symbol']

        try:
            spotPrice = float(markets[spotSymbol]['info']['price'])
        except KeyError:
            continue

        futurePrice = float(i['info']['price'])

        higher = max(spotPrice, futurePrice)
        lower = min(spotPrice, futurePrice)
        basis = (higher-lower) / higher * 100

        if basis > 3:
            print(f'{spotSymbol}: spot {spotPrice}, {futureSymbol} {futurePrice}, basis {round(basis, 1)} %')


print('done')
