import json

from brownie import *
import os
import util
from classes import Token
import datetime
import time

with open('avalanche_addresses.json') as f:
    addresses = json.load(f)

SNOWTRACE_API_KEY = "JCGRVAFIADSVISFU675XCRNRNKII4Z7UBJ"
os.environ["SNOWTRACE_TOKEN"] = SNOWTRACE_API_KEY

network.connect('ganache-avax-fork')

dai = Token(addresses['DAI'], 'Avalanche Token: DAI')
mim = Token(addresses['MIM'], 'Avalanche Token: MIM')
usdc = Token(addresses['USDC'], 'Avalanche Token: USDC')
usdt = Token(addresses['USDT'], 'Avalanche Token: USDT')
wavax = Token(addresses['WAVAX'], 'Avalanche Token: WAVAX')
router = util.contract_load(addresses['TRADER_JOE_ROUTER'], 'Avalanche Contract: TRADER JOE')

token_pairs = [
    (dai, mim),
    (mim, dai),
    (dai, usdc),
    (usdc, dai),
    (usdt, dai),
    (dai, usdt),
    (usdc, usdt),
    (usdt, usdc),
    (usdt, mim),
    (mim, usdt),
    (usdc, mim),
    (mim, usdc),
]

while True:
    for pair in token_pairs:
        token_in = pair[0]
        token_out = pair[1]
        qty_out = (
                router.getAmountsOut(
                    1 * (10 ** token_in.decimals),
                    [
                        token_in.address,
                        wavax.address,
                        token_out.address,
                    ],
                )[-1] / (10 ** token_out.decimals)
        )

        if qty_out > 1:
            ts = datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
            print(f"{ts} {token_in.symbol} → {token_out.symbol}: ({qty_out:.6f})")

        time.sleep(0.1)
