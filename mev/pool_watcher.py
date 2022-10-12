from brownie import *
import brownie
import os
import sqlite3
import websockets
import json
import asyncio

SNOWTRACE_API_KEY = "JCGRVAFIADSVISFU675XCRNRNKII4Z7UBJ"
os.environ["SNOWTRACE_TOKEN"] = SNOWTRACE_API_KEY

network.connect('avax-main-quicknode-ws')


def get_pools(table):
    conn = sqlite3.connect('./pools.db')
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM {table};')
    return cur.fetchall()


async def monitor_pool(address):
    async for websocket in websockets.connect(uri=brownie.web3.provider.endpoint_uri):
        try:
            await websocket.send(
                json.dumps({
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": [
                        "logs",
                        {"address": address}
                    ]
                })
            )
            subscribe_result = await websocket.recv()
            print(subscribe_result)

            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30)
                    tx_hash = json.loads(message)["params"]["result"]
                    print(tx_hash)
                except websockets.WebSocketException:
                    break  # escape the loop to reconnect
                except Exception as e:
                    print(e)

        except websockets.WebSocketException:
            print("Reconnecting...")
            continue
        except Exception as e:
            print(e)


async def main():
    await asyncio.gather(
        asyncio.create_task(monitor_pool("0xeD8CBD9F0cE3C6986b22002F03c6475CEb7a6256")),
        asyncio.create_task(monitor_pool("0x87Dee1cC9FFd464B79e058ba20387c1984aed86a")),
        asyncio.create_task(monitor_pool("0xA389f9430876455C36478DeEa9769B7Ca4E3DDB1")),
        asyncio.create_task(monitor_pool("0x781655d802670bbA3c89aeBaaEa59D3182fD755D"))
    )


if __name__ == "__main__":
    print('Monitoring pools...')
    asyncio.run(main())
