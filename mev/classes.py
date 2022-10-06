import util


class Token:
    def __init__(self, address, alias):
        contract = util.load_contract(address, alias)
        self.address = contract.address
        self.symbol = contract.symbol()
        self.decimals = contract.decimals()
