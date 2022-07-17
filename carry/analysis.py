import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import util
import config

font = {  # 'family': 'serif',
    # 'color':  'darkred',
    'weight': 'normal',
    'size': 12,
}

all_expirations = util.get_all_expirations()

results_dict = {}  # {coin : [profits]}

for expiration in all_expirations:
    path = f'{config.RESULTS_FOLDER}/{expiration}.csv'
    df = pd.read_csv(path)

    d = df.to_dict('records')
    for i in d:
        i.pop('Unnamed: 0', None)  # todo remove this
        if i['Coin'] in results_dict:
            results_dict[i['Coin']].append(i['Profit'])
        else:
            results_dict[i['Coin']] = [i['Profit']]

    # fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    # data = np.array(df['Profit'])
    # bins = np.arange(data.min(), data.max(), 3000)
    # ax.hist(data, bins, rwidth=0.7, density=True)
    # # ax.set_xticks(bins + 0.5)
    # # ax.set_xlim([0.1, data.max() + 0.9])
    # ax.set_title(expiration, fontdict=font)
    # ax.set_ylabel('Frequency', fontdict=font)
    # ax.set_xlabel('Profit', fontdict=font)

profits = []
for k, v in results_dict.items():
    profits.append(v)

# Multiple box plots on one Axes
fig, ax = plt.subplots(figsize=(12, 6))
ax.set_xticklabels(results_dict.keys(), rotation=90, fontsize=8)
ax.boxplot(profits)
# ax.set_yscale('log')

plt.show()
