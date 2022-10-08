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


traderjoe_router = load_contract('0x60aE616a2155Ee3d9A68541Ba4544862310933d4', 'traderjoe')
pool = load_contract('0x033c3fc1fc13f803a233d262e24d1ec3fd4efb48', 'sspell-spell')
sspell = load_contract(pool.token0(), 'sSPELL')
spell = load_contract(pool.token1(), 'SPELL')
wavax_address = '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7'
sushi_router = Contract.from_explorer('0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506')


def main():
    chain.revert()
    user = accounts[0]
    FlashBorrow.deploy({'from': user})
    flas_borrow_contract = FlashBorrow[0]

    sspell_borrow_amount = 10000 * 10 ** 18
    spell_repay_amount = traderjoe_router.getAmountsIn(sspell_borrow_amount, [spell.address, sspell.address])[0]
    print(f'In order to borrow {sspell_borrow_amount} sSPELL, it is needed to repay with {spell_repay_amount} SPELL')

    print(f'Swapping AVAX for {spell_repay_amount} SPELL with Sushi')

    sushi_router.swapETHForExactTokens(spell_repay_amount, [wavax_address, spell.address], user.address,
                                       99999999999999999999999, {'from': user, 'value': 1 * 10 ** 18})

    print(f'User SPELL balance: {spell.balanceOf(user.address)}')

    print('Transfer SPELL from user to contract')
    spell.transfer(flas_borrow_contract.address, spell.balanceOf(user), {'from': user})

    print(f'Flash Borrow Contract SPELL balance: {spell.balanceOf(flas_borrow_contract.address)}')

    print(f'Executing flash swap: borrow {sspell_borrow_amount} sSPELL, repay with {spell_repay_amount} SPELL')
    tx = flas_borrow_contract.execute(pool.address,
                                      sspell.address,
                                      sspell_borrow_amount,
                                      spell.address,
                                      spell_repay_amount,
                                      {'from': user})

    print(tx.info())

    print(f'Flash Borrow Contract SPELL balance: {spell.balanceOf(flas_borrow_contract.address)}')
    print(f'Flash Borrow Contract sSPELL balance: {sspell.balanceOf(flas_borrow_contract.address)}')