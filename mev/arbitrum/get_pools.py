from brownie import accounts, network, multicall, Contract, web3, exceptions, chain
import sys
import os
import warnings
import sqlite3

warnings.filterwarnings("ignore", category=exceptions.BrownieCompilerWarning)

BROWNIE_NETWORK = "arbitrum-main-quicknode"

FLUSH_INTERVAL = 500


os.environ["ARBISCAN_TOKEN"] = "XRM4V641WUSCDEM9VIHEHRZPTNAG23FAX9"


def main():
    try:
        network.connect(BROWNIE_NETWORK)
    except:
        sys.exit("Could not connect! Verify your Brownie network settings using 'brownie networks list'")

    exchanges = [
        # {
        #     "name": "SushiSwap",
        #     "table_name": "sushiswap",
        #     "factory_address": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
        # },
        {
            "name": "Uniswap",
            "table_name": "uniswap",
            "factory_address": "0x1F98431c8aD98523631AE4a59f267346ea31F984"
        },
        # {
        #     "name": "Pangolin",
        #     "table_name": "pangolin_pools",
        #     "factory_address": "0xefa94DE7a4656D787667C749f7E1223D71E9FD88"
        # }
    ]

    for name, factory_address, table_name in [
        (exchange["name"], exchange["factory_address"], exchange["table_name"])
        for exchange in exchanges
    ]:

        print(f"Exchange {name}")
        factory = Contract.from_explorer(factory_address)

        # print(f"Retrieving ABI for typical LP")
        LP_ABI = Contract.from_explorer(factory.allPairs(0)).abi

        current_block = chain.height

        # count the number of pairs tracked by the factory
        pool_count = int(factory.allPairsLength())

        # build a list of pools, initially populated
        # with batched addresses gathered
        # from the factory (using multicall)
        pool_addresses = []

        with multicall(block_identifier=current_block):
            for i, pool_id in enumerate(range(pool_count)):
                if pool_id % FLUSH_INTERVAL == 0 and pool_id != 0:
                    multicall.flush()
                    print(f"Found {i}/{pool_count} pools")
                pool_addresses.append(factory.allPairs(pool_id))

        print("• Creating LP objects")
        pools = []
        for i, address in enumerate(pool_addresses):
            if i % FLUSH_INTERVAL == 0 and i != 0:
                multicall.flush()
                print(f"created {i}/{len(pool_addresses)} pool objects")
            pools.append(Contract.from_abi(
                name="",
                address=address,
                abi=LP_ABI
            ))

        print("• Getting token0 data")
        pool_token0_addresses = []
        with multicall(block_identifier=current_block):
            for i, pool_object in enumerate(pools):
                if i % FLUSH_INTERVAL == 0 and i != 0:
                    multicall.flush()
                    print(f"fetched {i}/{len(pools)} addresses")
                pool_token0_addresses.append(pool_object.token0())

        print("• Getting token1 data")
        pool_token1_addresses = []
        with multicall(block_identifier=current_block):
            for i, pool_object in enumerate(pools):
                if i % FLUSH_INTERVAL == 0 and i != 0:
                    multicall.flush()
                    print(f"fetched {i}/{len(pools)} addresses")
                pool_token1_addresses.append(pool_object.token1())

        # list of (pool, token0, token1)
        rows = list(
            zip(
                pool_addresses,
                pool_token0_addresses,
                pool_token1_addresses
            )
        )

        conn = sqlite3.connect('./pools.db')
        create_table(conn, table_name)
        for row in rows:
            insert(conn, table_name, *row)


def create_table(conn, table_name):
    query = f'''CREATE TABLE IF NOT EXISTS {table_name} (
            pool TEXT NOT NULL PRIMARY KEY,
            token0 TEXT NOT NULL,
            token1 TEXT NOT NULL);
            '''
    conn.execute(query)


def insert(conn, table_name, pool, token0, token1):
    query = f'''INSERT INTO {table_name} (pool, token0, token1)
            VALUES ('{pool}', '{token0}', '{token1}');
            '''
    try:
        conn.execute(query)
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    except Exception as e:
        print(f'Could not insert in {table_name} pool {pool}: {e}')


def get(conn, table_name):
    query = f'''SELECT * FROM {table_name};'''
    cur = conn.cursor()
    cur.execute(query)
    return cur.fetchall()


main()
