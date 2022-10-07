from brownie import *
import time
import util
import os
import json

SNOWTRACE_API_KEY = "JCGRVAFIADSVISFU675XCRNRNKII4Z7UBJ"
os.environ["SNOWTRACE_TOKEN"] = SNOWTRACE_API_KEY

with open('avalanche_addresses.json') as f:
    addresses = json.load(f)

network.connect('avax-main-quicknode-ws')

token0 = util.load_contract(addresses['USDC'], 'USDC')
token1 = util.load_contract(addresses['WAVAX'], 'WAVAX')

lp_trader_joe = util.load_contract('0xA389f9430876455C36478DeEa9769B7Ca4E3DDB1', 'Trader Joe USDC-WAVAX')
filter_trader_joe = web3.eth.contract(address=lp_trader_joe.address, abi=lp_trader_joe.abi).events.Sync.createFilter(
    fromBlock='latest')

lp_sushi = util.load_contract('0x4ed65dAB34d5FD4b1eb384432027CE47E90E1185', 'Sushi USDC-WAVAX')
filter_sushi = web3.eth.contract(address=lp_sushi.address, abi=lp_sushi.abi).events.Sync.createFilter(
    fromBlock='latest')

lp_pangolin = util.load_contract('0xbd918Ed441767fe7924e99F6a0E0B568ac1970D9', 'Pangolin USDC-WAVAX')
filter_pangolin = web3.eth.contract(address=lp_pangolin.address, abi=lp_pangolin.abi).events.Sync.createFilter(
    fromBlock='latest')

print('Start monitoring pools...')
while True:
    res = filter_trader_joe.get_new_entries()
    if len(res) > 0:
        res = res[-1]
        reserve0 = res['args']['reserve0'] / 10 ** token0.decimals()
        reserve1 = res['args']['reserve1'] / 10 ** token1.decimals()
        print(f'WAVAX/USDC Trader Joe quote: {round(reserve0 / reserve1, 2)}')

    res = filter_sushi.get_new_entries()
    if len(res) > 0:
        res = res[-1]
        reserve0 = res['args']['reserve0'] / 10 ** token0.decimals()
        reserve1 = res['args']['reserve1'] / 10 ** token1.decimals()
        print(f'WAVAX/USDC Sushi quote: {round(reserve0 / reserve1, 2)}')

    res = filter_pangolin.get_new_entries()
    if len(res) > 0:
        res = res[-1]
        reserve0 = res['args']['reserve0'] / 10 ** token0.decimals()
        reserve1 = res['args']['reserve1'] / 10 ** token1.decimals()
        print(f'WAVAX/USDC Pangolin quote: {round(reserve0 / reserve1, 2)}')

    time.sleep(0.1)
