from brownie import accounts, network, multicall, Contract, web3, exceptions, chain
import sys, os, csv
import copy
import warnings
import time

warnings.filterwarnings("ignore", category=exceptions.BrownieCompilerWarning)

BROWNIE_NETWORK = "avax-main-quicknode"

FLUSH_INTERVAL = 500

os.environ["SNOWTRACE_TOKEN"] = "JCGRVAFIADSVISFU675XCRNRNKII4Z7UBJ"


def main():
    try:
        network.connect(BROWNIE_NETWORK)
    except:
        sys.exit("Could not connect! Verify your Brownie network settings using 'brownie networks list'")

    exchanges = [
        {
            "name": "SushiSwap",
            "filename": "sushiswap_pools.csv",
            "factory_address": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
        },
        {
            "name": "TraderJoe",
            "filename": "traderjoe_pools.csv",
            "factory_address": "0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10"
        },
        {
            "name": "Pangolin",
            "filename": "pangolin_pools.csv",
            "factory_address": "0xefa94DE7a4656D787667C749f7E1223D71E9FD88"
        }
    ]

    for name, factory_address, filename in [
        (exchange["name"], exchange["factory_address"], exchange["filename"])
        for exchange in exchanges
    ]:

        print(f"Exchange {name}")

        try:
            factory = Contract.from_explorer(address=factory_address, silent=True)
        except exceptions.BrownieCompilerWarning:
            pass

            # print(f"Retrieving ABI for typical LP")
        try:
            LP_ABI = Contract.from_explorer(address=factory.allPairs(0), silent=True).abi
        except exceptions.BrownieCompilerWarning:
            pass

        current_block = chain.height

        # count the number of pairs tracked by the factory
        pool_count = int(factory.allPairsLength())

        # build a list of pools, initially populated 
        # with batched addresses gathered
        # from the factory (using multicall)
        pool_addresses = []

        start = time.time()
        with multicall(block_identifier=current_block):
            for pool_id in range(pool_count):
                if pool_id % FLUSH_INTERVAL == 0 and pool_id != 0:
                    multicall.flush()
                    # print(f"Found {i} pools")
                pool_addresses.append(factory.allPairs(pool_id))
        print(f'Found {len(pool_addresses)} pools in {time.time() - start} s')
        return

        # print("• Creating LP objects")
        # pools = []
        # for i, address in enumerate(pool_addresses):
        #     if i % FLUSH_INTERVAL == 0 and i != 0:
        #         print(f"created {i} pool objects")
        #     pools.append(Contract.from_abi(
        #         name="",
        #         address=address,
        #         abi=LP_ABI
        #     ))
        #     print(f"created {i} objects")
        #
        # print("• Getting token0 data")
        # pool_token0_addresses = []
        # with multicall(block_identifier=current_block):
        #     for i, pool_object in enumerate(pools):
        #         if i % FLUSH_INTERVAL == 0 and i != 0:
        #             multicall.flush()
        #             print(f"fetched {i} addresses")
        #         pool_token0_addresses.append(pool_object.token0())
        #     print(f"fetched {len(pools)} addresses")
        #
        # print("• Getting token1 data")
        # pool_token1_addresses = []
        # with multicall(block_identifier=current_block):
        #     for i, pool_object in enumerate(pools):
        #         if i % FLUSH_INTERVAL == 0 and i != 0:
        #             multicall.flush()
        #             print(f"fetched {i} addresses")
        #         pool_token1_addresses.append(pool_object.token1())
        #     print(f"fetched {len(pools)} addresses")
        #
        # rows = list(
        #     zip(
        #         pool_addresses,
        #         pool_token0_addresses,
        #         pool_token1_addresses,
        #     )
        # )
        #
        # print("• Saving pool data to CSV")
        # headers = [
        #     "pool_address",
        #     "token0",
        #     "token1",
        # ]
        # with open(filename, "w") as file:
        #     csv_writer = csv.writer(file)
        #     csv_writer.writerow(headers)
        #     csv_writer.writerows(rows)
        # return


main()
