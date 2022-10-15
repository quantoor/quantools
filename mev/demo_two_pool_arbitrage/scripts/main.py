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


def load_contract(address, alias):
    try:
        contract = Contract(alias)
    except ValueError:
        contract = Contract.from_explorer(address)
        contract.set_alias(alias)
    except Exception as e:
        print(f'Could not load contract {address}: {e}')
        return None
    return contract


def main():
    chain.snapshot()

    # constants
    spell_address = '0xCE1bFFBD5374Dac86a2893119683F4911a2F7814'
    sspell_address = '0x3Ee97d514BBef95a2f110e6B9b73824719030f7a'
    sushi_factory_address = '0xc35DADB65012eC5796536bD9864eD8773aBc74C4'
    sushi_router_address = '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
    sushi_pool_address = '0xE5cddBfd3A807691967e528f1d6b7f00b1919e6F'
    trader_joe_router_address = '0x60aE616a2155Ee3d9A68541Ba4544862310933d4'

    # check opportunity
    sushi_router = load_contract(sushi_router_address, 'sushi router')
    trader_joe_router = load_contract(trader_joe_router_address, 'trader joe router')

    res = sushi_router.getAmountsOut(10**18, [sspell_address, spell_address])
    print('Sushi sSPELL/SPELL:', res[0]/res[1])
    res = trader_joe_router.getAmountsOut(10**18, [sspell_address, spell_address])
    print('Trader Joe sPELL/SPELL:', res[0]/res[1])

    # deploy contract
    two_pool_arbitrage.deploy(sushi_factory_address, sushi_router_address, {'from': accounts[0]})

    print('Executing arbitrage...')
    # execute arbitrage
    try:
        tx = two_pool_arbitrage[0].execute(
            sushi_pool_address,
            spell_address,
            29312834720491373000000,
            [spell_address, sspell_address],
            trader_joe_router_address,
            {'from': accounts[0]}
        )

        print(tx.info())

        # check profit in balance
        sspell_contract = load_contract(sspell_address, 'sspell')
        print(sspell_contract.balanceOf(accounts[0]))

    except Exception as e:
        print(f'Error executing arbitrage: {e}')
    finally:
        print(f'Revert chain')
        chain.revert()
