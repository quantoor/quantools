from brownie import Contract
from common.logger import logger
from decimal import Decimal


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
