from common import util
import config as cfg
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


# all_expirations = util.get_historical_expirations()
path = f'{cfg.CACHE_FOLDER}/0930'
files = util.get_files_in_folder(path, '.csv')

print(files)

dfs = {}
for f in files:
    if "BTC" in f.stem or "ETH" in f.stem or "CEL" in f.stem:
        continue
    df = pd.read_csv(f)
    df['AbsBasis'] = abs((df['FutPrice'] - df['PerpPrice']) / df['PerpPrice'] * 100)
    df['AbsBasis'] = df['AbsBasis'].ewm(span=24).mean()
    df['AbsBasisNorm'] = df['AbsBasis'] / df['AbsBasis'].max()
    df['Date'] = [datetime.fromtimestamp(ts) for ts in df['Timestamp']]
    dfs[f.stem] = df

plt.figure()
for df in dfs.values():
    plt.plot(df['Date'], df['AbsBasis'])
    # print(df['AbsBasisNorm'].iat[-1])
# plt.legend(dfs.keys())
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
