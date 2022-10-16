from brownie import *
import brownie
import os
import websockets
import json
import asyncio
import eth_abi
import web3
import util
from database_client import DatabaseClient

os.environ["SNOWTRACE_TOKEN"] = "JCGRVAFIADSVISFU675XCRNRNKII4Z7UBJ"

network.connect('avax-main-quicknode-ws')

SUSHI = 'Sushiswap'
PANGOLIN = 'Pangolin'
TRADER_JOE = 'Trader Joe'

db_client = DatabaseClient('./pools.db')
POOL_TO_PAIR_SUSHI = db_client.get_pool_to_pair_dict('sushiswap_pools')
POOL_TO_PAIR_PANGOLIN = db_client.get_pool_to_pair_dict('pangolin_pools')
POOL_TO_PAIR_TRADER_JOE = db_client.get_pool_to_pair_dict('traderjoe_pools')
POOL_TO_PAIR_TRADER_ALL = POOL_TO_PAIR_SUSHI | POOL_TO_PAIR_PANGOLIN | POOL_TO_PAIR_TRADER_JOE
TOKENS = db_client.get_tokens_info()

arbitrage_dict = {}


def get_pool_dex(address) -> str:
    if address in POOL_TO_PAIR_SUSHI:
        return SUSHI
    if address in POOL_TO_PAIR_PANGOLIN:
        return PANGOLIN
    if address in POOL_TO_PAIR_TRADER_JOE:
        return TRADER_JOE


def ignore_pool(address) -> bool:
    # ignore tokens not verified
    if address in POOL_TO_PAIR_TRADER_ALL:
        pair = POOL_TO_PAIR_TRADER_ALL[address]
    else:
        # raise Exception(f'pool {address} not found')
        return True

    try:
        if not TOKENS[pair[0]]['verified']:
            return True
        if not TOKENS[pair[1]]['verified']:
            return True
        return False

    except Exception as e:
        print('Error in ignore pool', e)
        return True


async def monitor_pools():
    async for websocket in websockets.connect(uri=brownie.web3.provider.endpoint_uri):
        await websocket.send(
            json.dumps({
                "id": 1,
                "method": "eth_subscribe",
                "params": [
                    "logs",
                    {"topics": [web3.Web3().keccak(text="Sync(uint112,uint112)").hex()]}
                ]
            })
        )
        subscribe_result = await websocket.recv()
        print(subscribe_result)

        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=30)
            except websockets.WebSocketException:
                break  # escape the loop to reconnect
            except Exception as e:
                print('Error', e)
                continue

            result = json.loads(message)["params"]["result"]
            address = result["address"]

            if ignore_pool(address):
                continue

            try:
                token0_address, token1_address = POOL_TO_PAIR_TRADER_ALL[address]
                token0 = TOKENS[token0_address]
                token1 = TOKENS[token1_address]

                data = result["data"]
                res = eth_abi.decode_single('(uint112,uint112)', bytes.fromhex(data[2:]))
                res0 = res[0] / 10 ** token0['decimals']
                res1 = res[1] / 10 ** token1['decimals']

                pair_symbol = token0['symbol'] + '/' + token1['symbol']
                quote = res1 / res0

                # save quotes
                key = frozenset[token0_address, token1_address]
                if key in arbitrage_dict:
                    arbitrage_dict[key][address] = {
                        'DEX': get_pool_dex(address), 'pair_symbol': pair_symbol, 'quote': quote
                    }
                else:
                    arbitrage_dict[key] = {
                        address: {'DEX': get_pool_dex(address), 'pair_symbol': pair_symbol, 'quote': quote}
                    }

                print(arbitrage_dict[key])
                # print(f'''[{get_pool_dex(address)}] {pair_symbol}: {quote}''')

            except Exception as e:
                print('Error', e)


async def main():
    await asyncio.gather(
        asyncio.create_task(monitor_pools())
    )


if __name__ == "__main__":
    print('Monitoring pools...')
    asyncio.run(main())
