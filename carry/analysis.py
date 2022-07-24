import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from common import util
import config

font = {  # 'family': 'serif',
    # 'color':  'darkred',
    'weight': 'normal',
    'size': 12,
}

all_expirations = util.get_historical_expirations()

results_by_coin = {}  # {coin : [profits]}
results_by_expiration = {}  # {expiration: [profits]}

for expiration in all_expirations:
    path = f'{config.RESULTS_FOLDER}/{expiration}.csv'
    df = pd.read_csv(path)
    d = df.to_dict('records')

    results_by_expiration[expiration] = []

    for i in d:
        if i['Coin'] in results_by_coin:
            results_by_coin[i['Coin']].append(i['Profit'])
        else:
            results_by_coin[i['Coin']] = [i['Profit']]

        results_by_expiration[expiration].append(i['Profit'])

    # fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    # data = np.array(df['Profit'])
    # bins = np.arange(data.min(), data.max(), 3000)
    # ax.hist(data, bins, rwidth=0.7, density=True)
    # # ax.set_xticks(bins + 0.5)
    # # ax.set_xlim([0.1, data.max() + 0.9])
    # ax.set_title(expiration, fontdict=font)
    # ax.set_ylabel('Frequency', fontdict=font)
    # ax.set_xlabel('Profit', fontdict=font)

coin_to_mean_of_profits = {coin: np.mean(profits) for coin, profits in results_by_coin.items()}
coin_sorted_by_mean_of_profit = dict(sorted(coin_to_mean_of_profits.items(), key=lambda item: item[1]))
data = {coin: results_by_coin[coin] for coin in coin_sorted_by_mean_of_profit.keys()}

fig, ax = plt.subplots(figsize=(12, 6))
fig.suptitle('Profits by coin')
ax.set_xticklabels(data.keys(), rotation=90, fontsize=8)
ax.boxplot(list(data.values()))
# ax.set_yscale('log')

fig1, ax = plt.subplots(figsize=(12, 6))
fig1.suptitle('Profits by expiration')
ax.set_xticklabels(results_by_expiration.keys(), rotation=90, fontsize=8)
ax.boxplot(list(results_by_expiration.values()))

plt.show()
