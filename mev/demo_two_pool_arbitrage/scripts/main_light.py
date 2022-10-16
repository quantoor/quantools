from brownie import *
import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

SNOWTRACE_API_KEY = "JCGRVAFIADSVISFU675XCRNRNKII4Z7UBJ"
os.environ["SNOWTRACE_TOKEN"] = SNOWTRACE_API_KEY

try:
    network.connect('ganache-avax-fork')
except:
    pass


def main():
    print(f'Snaptshot chain at {chain.height}')
    chain.snapshot()

    # deploy contract
    two_pool_arbitrage_light.deploy({'from': accounts[0]})

    print('Executing arbitrage...')
    # execute arbitrage
    try:
        tx = two_pool_arbitrage_light[0].execute({'from': accounts[0]})

        print(tx.info())

        # check profit in balance
        sspell_contract = Contract('0x3Ee97d514BBef95a2f110e6B9b73824719030f7a')
        print(sspell_contract.balanceOf(accounts[0]))

    except Exception as e:
        print(f'Error executing arbitrage: {e}')

    finally:
        height = chain.revert()
        print(f'Revert chain to {height}')
