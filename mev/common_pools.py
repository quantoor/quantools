from brownie import *
import time
import util
import os
import sqlite3
from classes import LP
from common.logger import logger


SNOWTRACE_API_KEY = "JCGRVAFIADSVISFU675XCRNRNKII4Z7UBJ"
os.environ["SNOWTRACE_TOKEN"] = SNOWTRACE_API_KEY

network.connect('avax-main-quicknode-ws')

logger.add_console()
logger.add_file('./log')
logger.info('Start common pools')


def get_pools(table):
    conn = sqlite3.connect('./pools.db')
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM {table};')
    return [(x[0].lower(), x[1].lower(), x[2].lower()) for x in cur.fetchall()]


pair_to_pool_sushi = {(i[1], i[2]): i[0] for i in get_pools('sushiswap_pools')}
pair_to_pool_traderjoe = {(i[1], i[2]): i[0] for i in get_pools('traderjoe_pools')}
pair_to_pool_pangolin = {(i[1], i[2]): i[0] for i in get_pools('pangolin_pools')}

sushi_abi = util.load_contract(list(pair_to_pool_sushi.values())[0], 'sushiabi').abi
traderjoe_abi = util.load_contract(list(pair_to_pool_traderjoe.values())[0], 'traderjoeabi').abi
pangolin_abi = util.load_contract(list(pair_to_pool_pangolin.values())[0], 'pangolinabi').abi

common_pairs = []

for pair in pair_to_pool_traderjoe:
    pair_inv = (pair[1], pair[0])

    if pair in pair_to_pool_sushi or pair_inv in pair_to_pool_sushi:
        common_pairs.append(pair)
    elif pair in pair_to_pool_pangolin or pair_inv in pair_to_pool_pangolin:
        common_pairs.append(pair)

arbitrage_pools = []
for i, pair in enumerate(common_pairs):
    if i % 50 == 0:
        print(f'Pair {i}/{len(common_pairs)}')
    
    arbitrage_pool = []

    count = 0

    if pair in pair_to_pool_sushi:
        pool = pair_to_pool_sushi[pair]
        arbitrage_pool.append(LP(pool))
        count += 1

    if pair in pair_to_pool_traderjoe:
        pool = pair_to_pool_traderjoe[pair]
        arbitrage_pool.append(LP(pool))
        count += 1

    if pair in pair_to_pool_pangolin:
        pool = pair_to_pool_pangolin[pair]
        if count < 2:
            arbitrage_pool.append(LP(pool))
        else:
            arbitrage_pool.append('empty')

    arbitrage_pools.append(arbitrage_pool)

arbitrage_pools_2 = [p for p in arbitrage_pools if len(p) == 2]

filters_to_pools = {}

print('Creating filters...')
for i, lp_pair in enumerate(arbitrage_pools_2):
    if i % 50 == 0:
        print(f'Filter {i}/{len(common_pairs)}')
    lp1, lp2 = lp_pair
    f1 = web3.eth.contract(address=web3.toChecksumAddress(lp1.address), abi=lp1.abi).events.Sync.createFilter(fromBlock='latest')
    f2 = web3.eth.contract(address=web3.toChecksumAddress(lp2.address), abi=lp2.abi).events.Sync.createFilter(fromBlock='latest')
    filters_to_pools[f1] = lp1
    filters_to_pools[f2] = lp2


last_prices = {}

logger.info('Monitoring pools...')
while True:
    start = time.time()
    for f, lp in filters_to_pools.items():
        res = f.get_new_entries()
        # if len(res) > 0:
        #     res = res[-1]
        #     reserve0 = res['args']['reserve0'] / 10 ** lp.token0.decimals
        #     reserve1 = res['args']['reserve1'] / 10 ** lp.token1.decimals
        #     logger.info(f'{lp.address} {lp.token0.symbol}/{lp.token1.symbol}: {round(reserve0 / reserve1, 4)}')
    print('elapsed time', time.time() - start)


# pools_sushi = [t[0] for t in res if (t[1].lower(), t[2].lower()) in pairs]
# pools_contract_sushi = [LP(lp, lp[2:]) for lp in pools_sushi]
# abi_sushi = util.load_contract(pools_sushi[0], 'sushiabi').abi
# filters_sushi = {web3.eth.contract(address=lp.address, abi=abi_sushi).events.Sync.createFilter(fromBlock='latest'): lp
#                  for lp in pools_contract_sushi}
#
# res = get_pools('traderjoe_pools')
# pools_traderjoe = [t[0] for t in res if (t[1].lower(), t[2].lower()) in pairs]
# pools_contract_traderjoe = [LP(lp, lp[2:]) for lp in pools_traderjoe]
# abi_traderjoe = util.load_contract(pools_traderjoe[0], 'traderjoeabi').abi
# filters_traderjoe = {web3.eth.contract(address=lp.address, abi=abi_traderjoe).events.Sync.createFilter(fromBlock='latest'): lp
#                      for lp in pools_contract_traderjoe}
#
# res = get_pools('pangolin_pools')
# pools_pangolin = [t[0] for t in res if (t[1].lower(), t[2].lower()) in pairs]
# pools_contract_pangolin = [LP(lp, lp[2:]) for lp in pools_pangolin]
# abi_pangolin = util.load_contract(pools_pangolin[0], 'pangolinabi').abi
# filters_pangolin = {web3.eth.contract(address=lp.address, abi=abi_pangolin).events.Sync.createFilter(fromBlock='latest'): lp
#                     for lp in pools_contract_pangolin}

# print('Monitoring pools...')
#
# while True:
#     for f, lp in filters_sushi.items():
#         res = f.get_new_entries()
#         if len(res) > 0:
#             res = res[-1]
#             reserve0 = res['args']['reserve0'] / 10 ** lp.token0.decimals
#             reserve1 = res['args']['reserve1'] / 10 ** lp.token1.decimals
#             if reserve0/reserve1 < 1:
#                 reserve0, reserve1 = reserve1, reserve0
#             print(f'Sushiswap {lp.token0.symbol}/{lp.token1.symbol}: {round(reserve0 / reserve1, 4)}')
#
#     for f, lp in filters_traderjoe.items():
#         res = f.get_new_entries()
#         if len(res) > 0:
#             res = res[-1]
#             reserve0 = res['args']['reserve0'] / 10 ** lp.token0.decimals
#             reserve1 = res['args']['reserve1'] / 10 ** lp.token1.decimals
#             if reserve0/reserve1 < 1:
#                 reserve0, reserve1 = reserve1, reserve0
#             print(f'Trader Joe {lp.token0.symbol}/{lp.token1.symbol}: {round(reserve0 / reserve1, 4)}')
#
#     for f, lp in filters_pangolin.items():
#         res = f.get_new_entries()
#         if len(res) > 0:
#             res = res[-1]
#             reserve0 = res['args']['reserve0'] / 10 ** lp.token0.decimals
#             reserve1 = res['args']['reserve1'] / 10 ** lp.token1.decimals
#             if reserve0/reserve1 < 1:
#                 reserve0, reserve1 = reserve1, reserve0
#             print(f'Pangolin {lp.token0.symbol}/{lp.token1.symbol}: {round(reserve0 / reserve1, 4)}')
#
#     time.sleep(0.1)
