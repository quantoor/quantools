from brownie import *
import brownie
import os
import websockets
import json
import asyncio
import eth_abi
import web3
import util


os.environ["SNOWTRACE_TOKEN"] = "JCGRVAFIADSVISFU675XCRNRNKII4Z7UBJ"

network.connect('avax-main-quicknode-ws')


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

            try:
                pool = util.load_contract(address, address[2:])
                token0 = util.load_contract(pool.token0(), pool.token0()[2:])
                token1 = util.load_contract(pool.token1(), pool.token1()[2:])

                data = result["data"]
                res = eth_abi.decode_single('(uint112,uint112)', bytes.fromhex(data[2:]))
                res0 = res[0] / 10 ** token0.decimals()
                res1 = res[1] / 10 ** token1.decimals()
                print(f'{token0.symbol()}/{token1.symbol()}', res1 / res0)
            except Exception as e:
                print('Error', e)


async def main():
    await asyncio.gather(
        asyncio.create_task(monitor_pools())
    )


if __name__ == "__main__":
    print('Monitoring pools...')
    asyncio.run(main())
