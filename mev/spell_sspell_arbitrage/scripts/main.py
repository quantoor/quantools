from brownie import *
import os
import warnings
from fractions import Fraction
from scipy import optimize

# 21141181
LIVE = True

warnings.filterwarnings("ignore", category=DeprecationWarning)

os.environ["SNOWTRACE_TOKEN"] = "JCGRVAFIADSVISFU675XCRNRNKII4Z7UBJ"

ARB_CONTRACT_ADDRESS = "0xF6aA141f9D032C2d74415e1cb5E3aFE271726111"

if LIVE:
    from abi import ABI

    try:
        network.connect('avax-main')
    except Exception as e:
        # sys.exit(f'Could not connect to network: {e}')
        pass

spell = Contract('0xCE1bFFBD5374Dac86a2893119683F4911a2F7814')
sspell = Contract('0x3Ee97d514BBef95a2f110e6B9b73824719030f7a')
# sushi_factory_address = '0xc35DADB65012eC5796536bD9864eD8773aBc74C4'
sushi_router = Contract('0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506')
trader_joe_router = Contract('0x60aE616a2155Ee3d9A68541Ba4544862310933d4')
sushi_pool = Contract('0xE5cddBfd3A807691967e528f1d6b7f00b1919e6F')
trader_joe_pool = Contract('0x033C3Fc1fC13F803A233D262e24d1ec3fd4EFB48')


def two_pool_arbitrage_profit(pool0_reserves, pool1_reserves, borrow_amount, borrow_token0):
    def getAmountIn(
            reserves_token0,
            reserves_token1,
            fee,
            token_out_quantity,
            token0_in
    ):
        if token0_in:
            return int(
                (reserves_token0 * token_out_quantity)
                // ((1 - fee) * (reserves_token1 - token_out_quantity))
                + 1
            )
        else:
            return int(
                (reserves_token1 * token_out_quantity)
                // ((1 - fee) * (reserves_token0 - token_out_quantity))
                + 1
            )

    def getAmountOut(
            reserves_token0,
            reserves_token1,
            fee,
            token_in_quantity,
            token0_in
    ):
        if token0_in:
            return int(reserves_token1 * token_in_quantity * (1 - fee)) // int(
                reserves_token0 + token_in_quantity * (1 - fee)
            )
        else:
            return int(reserves_token0 * token_in_quantity * (1 - fee)) // int(
                reserves_token1 + token_in_quantity * (1 - fee)
            )

    # Borrow pool reserves
    x0a, y0a = pool0_reserves

    # Swap pool reserves
    x0b, y0b = pool1_reserves

    # get repayment INPUT at borrow_amount OUTPUT
    flash_repay_amount = getAmountIn(
        reserves_token0=x0a,
        reserves_token1=y0a,
        fee=Fraction(3, 1000),
        token_out_quantity=borrow_amount,
        token0_in=False if borrow_token0 else True  # False
    )

    swap_amount_out = getAmountOut(
        reserves_token0=x0b,
        reserves_token1=y0b,
        fee=Fraction(3, 1000),
        token_in_quantity=borrow_amount,
        token0_in=True if borrow_token0 else False  # True
    )

    return swap_amount_out - flash_repay_amount


def optimize_two_pool_arbitrage(pool0_reserves, pool1_reserves, borrow_token0):
    y0a = pool0_reserves[1]

    bounds = (1, y0a)

    bracket = (0.01 * y0a, 0.05 * y0a)

    result = optimize.minimize_scalar(
        lambda x: -float(two_pool_arbitrage_profit(pool0_reserves, pool1_reserves, x, borrow_token0)),
        method="bounded",
        bounds=bounds,
        bracket=bracket
    )

    return result.x, -result.fun


def arbitrage():
    res = sushi_router.getAmountsOut(10 ** 18, [spell.address, sspell.address])
    sushi_quote = res[0] / res[1]
    print('Sushi sSPELL/SPELL:', sushi_quote)

    res = trader_joe_router.getAmountsOut(10 ** 18, [spell.address, sspell.address])
    trader_joe_quote = res[0] / res[1]
    print('Trader Joe sPELL/SPELL:', trader_joe_quote)

    # Print reserves
    sushi_reserves = sushi_pool.getReserves()[:2]
    trader_joe_reserves = trader_joe_pool.getReserves()[:2]

    print('Sushi reserves', sushi_reserves)
    print('Trader Joe reserves', trader_joe_reserves)

    # borrow sSPELL if the quote of sSPELL/SPELL in smaller on Sushi
    if sushi_quote < trader_joe_quote:
        borrow_token0 = True
        borrow_token_address = sspell.address
        swap_path = [sspell.address, spell.address]
    else:
        borrow_token0 = False
        borrow_token_address = spell.address
        swap_path = [spell.address, sspell.address]

    borrow_amount_opt, profit_opt = optimize_two_pool_arbitrage(sushi_reserves, trader_joe_reserves, borrow_token0)
    print('Optimal results', borrow_amount_opt / 10 ** 18, profit_opt / 10 ** 18)

    if profit_opt > 1000 * 10**18:
        if LIVE:
            spell_sspell_arbitrage = Contract.from_abi(
                name="",
                address=ARB_CONTRACT_ADDRESS,
                abi=ABI,
            )

            tx = spell_sspell_arbitrage.execute(
                sushi_pool.address,
                borrow_token_address,
                borrow_amount_opt,
                swap_path,
                trader_joe_router,
                {'from': accounts[0]}
            )
        else:
            spell_sspell_arbitrage.deploy(sushi_router.address, {'from': accounts[0]})

            tx = spell_sspell_arbitrage[0].execute(
                sushi_pool.address,
                borrow_token_address,
                borrow_amount_opt,
                swap_path,
                trader_joe_router,
                {'from': accounts[0]}
            )

        print(tx.info())

        # check profit in balance
        print('SPELL balance', spell.balanceOf(accounts[0]))
        print('sPELL balance', sspell.balanceOf(accounts[0]))


def main():
    try:
        if not LIVE:
            chain.snapshot()
            print('Snapshot chain at', chain.height)
        arbitrage()
    except Exception as e:
        print('ERROR', e)
    finally:
        if not LIVE:
            print('Revert chain to', chain.revert())


main()
