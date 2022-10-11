from brownie import *
import time
import util
import os
import sqlite3
from classes import LP

SNOWTRACE_API_KEY = "JCGRVAFIADSVISFU675XCRNRNKII4Z7UBJ"
os.environ["SNOWTRACE_TOKEN"] = SNOWTRACE_API_KEY

network.connect('avax-main-quicknode-ws')

DAI = "0xd586e7f844cea2f87f50152665bcbc2c279d8d70".lower()
MIM = "0x130966628846bfd36ff31a822705796e8cb8c18d".lower()
USDC = "0xa7d7079b0fead91f3e65f86e8915cb59c1a4c664".lower()
USDT = "0xc7198437980c041c805a1edcba50c1ce5db95118".lower()
WAVAX = "0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7".lower()

pairs = [
    (DAI, WAVAX), (WAVAX, DAI),
    (MIM, WAVAX), (WAVAX, MIM),
    (USDC, WAVAX), (WAVAX, USDC),
    (USDT, WAVAX), (WAVAX, USDT)
]


def get_pools(table):
    conn = sqlite3.connect('./pools.db')
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM {table};')
    return cur.fetchall()


res = get_pools('sushiswap_pools')
pools_sushi = [t[0] for t in res if (t[1].lower(), t[2].lower()) in pairs]
pools_contract_sushi = [LP(lp, lp[2:]) for lp in pools_sushi]
abi_sushi = util.load_contract(pools_sushi[0], 'sushiabi').abi
filters_sushi = {web3.eth.contract(address=lp.address, abi=abi_sushi).events.Sync.createFilter(fromBlock='latest'): lp
                 for lp in pools_contract_sushi}

res = get_pools('traderjoe_pools')
pools_traderjoe = [t[0] for t in res if (t[1].lower(), t[2].lower()) in pairs]
pools_contract_traderjoe = [LP(lp, lp[2:]) for lp in pools_traderjoe]
abi_traderjoe = util.load_contract(pools_traderjoe[0], 'traderjoeabi').abi
filters_traderjoe = {web3.eth.contract(address=lp.address, abi=abi_traderjoe).events.Sync.createFilter(fromBlock='latest'): lp
                     for lp in pools_contract_traderjoe}

res = get_pools('pangolin_pools')
pools_pangolin = [t[0] for t in res if (t[1].lower(), t[2].lower()) in pairs]
pools_contract_pangolin = [LP(lp, lp[2:]) for lp in pools_pangolin]
abi_pangolin = util.load_contract(pools_pangolin[0], 'pangolinabi').abi
filters_pangolin = {web3.eth.contract(address=lp.address, abi=abi_pangolin).events.Sync.createFilter(fromBlock='latest'): lp
                    for lp in pools_contract_pangolin}

print('Monitoring pools...')

while True:
    for f, lp in filters_sushi.items():
        res = f.get_new_entries()
        if len(res) > 0:
            res = res[-1]
            reserve0 = res['args']['reserve0'] / 10 ** lp.token0.decimals
            reserve1 = res['args']['reserve1'] / 10 ** lp.token1.decimals
            if reserve0/reserve1 < 1:
                reserve0, reserve1 = reserve1, reserve0
            print(f'Sushiswap {lp.token0.symbol}/{lp.token1.symbol}: {round(reserve0 / reserve1, 4)}')

    for f, lp in filters_traderjoe.items():
        res = f.get_new_entries()
        if len(res) > 0:
            res = res[-1]
            reserve0 = res['args']['reserve0'] / 10 ** lp.token0.decimals
            reserve1 = res['args']['reserve1'] / 10 ** lp.token1.decimals
            if reserve0/reserve1 < 1:
                reserve0, reserve1 = reserve1, reserve0
            print(f'Trader Joe {lp.token0.symbol}/{lp.token1.symbol}: {round(reserve0 / reserve1, 4)}')

    for f, lp in filters_pangolin.items():
        res = f.get_new_entries()
        if len(res) > 0:
            res = res[-1]
            reserve0 = res['args']['reserve0'] / 10 ** lp.token0.decimals
            reserve1 = res['args']['reserve1'] / 10 ** lp.token1.decimals
            if reserve0/reserve1 < 1:
                reserve0, reserve1 = reserve1, reserve0
            print(f'Pangolin {lp.token0.symbol}/{lp.token1.symbol}: {round(reserve0 / reserve1, 4)}')

    time.sleep(0.1)
