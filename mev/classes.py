import util


class Token:
    def __init__(self, address, alias):
        contract = util.contract_load(address, alias)
        self.address = contract.address
        self.symbol = contract.symbol()
        self.decimals = contract.decimals()
