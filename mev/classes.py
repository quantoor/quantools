import util


class Token:
    def __init__(self):
        self.address = None
        self.symbol = None
        self.name = None
        self.decimals = None
        self.verified = False

    def from_explorer(self, address: str):
        self.address = address
        try:
            contract = util.load_contract(address, address[2:])
        except ValueError:
            pass
        else:
            try:
                self.verified = True
                self.symbol = contract.symbol()
                self.name = contract.name()
                self.decimals = contract.decimals()
            except AttributeError as e:
                print('Error loading token from explorer', address, e)
        return self

    def from_fields(self, address, symbol, name, decimals):
        self.address = address
        self.symbol = symbol
        self.name = name
        self.decimals = decimals
        self.verified = True
        return self


class LP:
    def __init__(self, address):
        self._contract = util.load_contract(address, address[2:])
        self.address = address
        self._token0 = None
        self._token1 = None

    def get_reserves(self):
        return self._contract.getReserves()

    def get_tokens_out_from_tokens_in(self, quantity_token_in, is_token0_in, fee='0.003'):
        reserve_token0, reserve_token1, _ = self.get_reserves()

        if is_token0_in:
            quantity_token_in *= 10 ** self.token0.decimals
            amount_out = util.get_tokens_out_from_tokens_in(reserve_token0,
                                                            reserve_token1,
                                                            quantity_token0_in=quantity_token_in,
                                                            fee=fee)
            return amount_out / 10 ** self.token1.decimals
        else:
            quantity_token_in *= 10 ** self.token1.decimals
            amount_out = util.get_tokens_out_from_tokens_in(reserve_token0,
                                                            reserve_token1,
                                                            quantity_token1_in=quantity_token_in,
                                                            fee=fee)
            return amount_out / 10 ** self.token0.decimals

    @property
    def token0(self):
        if self._token0 is None:
            self._token0 = Token(self._contract.token0())
        return self._token0

    @token0.setter
    def token0(self, value):
        self._token0 = value

    @property
    def token1(self):
        if self._token1 is None:
            self._token1 = Token(self._contract.token1())
        return self._token1

    @token1.setter
    def token1(self, value):
        self._token1 = value

    @property
    def abi(self):
        return self._contract.abi
