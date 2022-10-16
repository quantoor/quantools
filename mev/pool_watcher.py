from brownie import *
import brownie
import os
import sqlite3
import websockets
import json
import asyncio
import eth_abi
import web3

SNOWTRACE_API_KEY = "JCGRVAFIADSVISFU675XCRNRNKII4Z7UBJ"
os.environ["SNOWTRACE_TOKEN"] = SNOWTRACE_API_KEY

network.connect('avax-main-quicknode-ws')


async def monitor_pools():
    async for websocket in websockets.connect(uri=brownie.web3.provider.endpoint_uri):
        try:
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
                    result = json.loads(message)["params"]["result"]

                    address = result["address"]
                    data = result["data"]
                    res = eth_abi.decode_single('(uint112,uint112)', bytes.fromhex(data[2:]))
                    print(address, res)
                except websockets.WebSocketException:
                    break  # escape the loop to reconnect
                except Exception as e:
                    print(e)

        except websockets.WebSocketException:
            print("Reconnecting...")
            continue
        except Exception as e:
            print('Error:', e)


async def main():
    await asyncio.gather(
        asyncio.create_task(monitor_pools())
    )


if __name__ == "__main__":
    print('Monitoring pools...')
    asyncio.run(main())
