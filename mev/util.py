from brownie import Contract
from common.logger import logger
from decimal import Decimal
from fractions import Fraction
from scipy import optimize


def load_contract(address, alias):
    try:
        contract = Contract(alias)
    except ValueError:
        contract = Contract.from_explorer(address)
        contract.set_alias(alias)
    except Exception as e:
        logger.error(f'Could not load contract {address}: {e}')
        return None
    return contract


def get_tokens_out_from_tokens_in(
        reserve_token0,
        reserve_token1,
        quantity_token0_in=0,
        quantity_token1_in=0,
        fee='0.003'
):
    fee = Decimal(fee)

    if quantity_token0_in and quantity_token1_in:
        raise Exception('Both token quantity in provided')

    if not quantity_token0_in and not quantity_token1_in:
        raise Exception('Quantity token in not provided')

    if quantity_token0_in:
        return (reserve_token1 * quantity_token0_in * (1 - fee)) // (reserve_token0 + quantity_token0_in * (1 - fee))

    if quantity_token1_in:
        return (reserve_token0 * quantity_token1_in * (1 - fee)) // (reserve_token1 + quantity_token1_in * (1 - fee))


def two_pool_arbitrage_profit(borrow_amount):
    def getAmountIn(
            reserves_token0,
            reserves_token1,
            fee,
            token_out_quantity,
            token_in
    ):
        """
        Calculates the required token INPUT of token_in for a target OUTPUT at current pool reserves.
        Uses the self.token0 and self.token1 pointers to determine which token is being swapped in
        and uses the appropriate formula

        Assumes token_in is token0, token_out is token1
        """

        if token_in == "token0":
            return int(
                (reserves_token0 * token_out_quantity)
                // ((1 - fee) * (reserves_token1 - token_out_quantity))
                + 1
            )

        if token_in == "token1":
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
            token_in
    ):
        """
        Calculates the expected token OUTPUT for a target INPUT at current pool reserves.
        Uses the self.token0 and self.token1 pointers to determine which token is being swapped in
        and uses the appropriate formula

        Assumes token_in is token1, token_out is token0
        """

        if token_in == "token0":
            return int(reserves_token1 * token_in_quantity * (1 - fee)) // int(
                reserves_token0 + token_in_quantity * (1 - fee)
            )

        if token_in == "token1":
            return int(reserves_token0 * token_in_quantity * (1 - fee)) // int(
                reserves_token1 + token_in_quantity * (1 - fee)
            )

    # SushiSwap reserves
    x0a = 47039249728141754753554675
    y0a = 57723736064967657010188311
    # TraderJoe reserves
    x0b = 35096943980497256569426582
    y0b = 42707590771017401912262893

    # get repayment INPUT at borrow_amount OUTPUT
    flash_repay_amount = getAmountIn(
        reserves_token0=x0a,
        reserves_token1=y0a,
        fee=Fraction(3, 1000),
        token_out_quantity=borrow_amount,
        token_in="token0",
    )

    swap_amount_out = getAmountOut(
        reserves_token0=x0b,
        reserves_token1=y0b,
        fee=Fraction(3, 1000),
        token_in_quantity=borrow_amount,
        token_in="token1",
    )

    return swap_amount_out - flash_repay_amount


def optimize_two_pool_arbitrage():
    y0a = 57723736064967657010188311

    bounds = (1, y0a)

    bracket = (0.01 * y0a, 0.05 * y0a)

    result = optimize.minimize_scalar(
        lambda x: -float(two_pool_arbitrage_profit(borrow_amount=x)),
        method="bounded",
        bounds=bounds,
        bracket=bracket
    )

    return result.x, -result.fun


if __name__ == '__main__':
    borrow = 29312834720491373000000
    profit = two_pool_arbitrage_profit(borrow)
    print(f"Borrow amount: {borrow / 10 ** 18}")
    print(f"Profit: {profit / 10 ** 18}")

    borrow_optimized, profit_optimized = optimize_two_pool_arbitrage()
    print(f"Optimized borrow amount: {borrow_optimized / 10 ** 18}")
    print(f"Profit optimized: {profit_optimized / 10 ** 18}")
