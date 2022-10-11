import util


class Token:
    def __init__(self, address, alias):
        contract = util.load_contract(address, alias)
        self.address = contract.address
        self.symbol = contract.symbol()
        self.decimals = contract.decimals()


class LP:
    def __init__(self, address, alias):
        self._lp = util.load_contract(address, alias)
        self.address = address
        self._alias = alias
        self._token0 = None
        self._token1 = None

    def get_reserves(self):
        return self._lp.getReserves()

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
            self._token0 = Token(self._lp.token0(), self._alias + 'token0')
        return self._token0

    @token0.setter
    def token0(self, value):
        self._token0 = value

    @property
    def token1(self):
        if self._token1 is None:
            self._token1 = Token(self._lp.token1(), self._alias + 'token1')
        return self._token1

    @token1.setter
    def token1(self, value):
        self._token1 = value
