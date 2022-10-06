from brownie import *
import time
import util
import os

SNOWTRACE_API_KEY = "JCGRVAFIADSVISFU675XCRNRNKII4Z7UBJ"
os.environ["SNOWTRACE_TOKEN"] = SNOWTRACE_API_KEY

network.connect('avax-main-quicknode-ws')

lp = util.load_contract('0xA389f9430876455C36478DeEa9769B7Ca4E3DDB1', 'USDC-AVAX')
token0 = util.load_contract(lp.token0(), 'USDC')
token1 = util.load_contract(lp.token1(), 'AVAx')

_filter = web3.eth.contract(address=lp.address, abi=lp.abi).events.Sync.createFilter(fromBlock='latest')

while True:
    res = _filter.get_new_entries()
    if len(res) > 0:
        res = res[-1]
        reserve0 = res['args']['reserve0'] / 10 ** token0.decimals()
        reserve1 = res['args']['reserve1'] / 10 ** token1.decimals()

        price = reserve0 / reserve1
        print(f'AVAX/USDC pool quote: {round(price, 2)}')

    time.sleep(0.1)
