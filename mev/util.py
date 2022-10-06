from brownie import Contract
from common.logger import logger


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
