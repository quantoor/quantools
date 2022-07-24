from common import util

markets = util.get_markets()

future_symbols = util.get_all_futures_symbols()
for future in future_symbols:

    coin, _ = util.get_coin_and_expiration_from_future_symbol(future)
    perp = util.get_perp_symbol(coin)

    if future not in markets.keys():
        continue

    future_price = markets[future]['price']
    perp_price = markets[perp]['price']

    basis = (future_price-perp_price)/perp_price*100
    if abs(basis) > 3:
        print(f'{future}: {round(basis, 2)} %')
