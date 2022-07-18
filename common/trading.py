class Position:
    def __init__(self, entry_price=None, size=0):
        self.entry_price = entry_price
        self.size = size

    def __str__(self):
        return f'Entry price: {self.entry_price}, size: {self.size}'

    def update(self, price: float, size: float):
        if self.entry_price is None:
            self.entry_price = price
        else:
            self.entry_price = (self.entry_price * self.size + price * size) / (self.size + size)
        self.size += size

    def reset(self):
        self.entry_price = None
        self.size = 0

    def get_pnl(self, price: float) -> float:
        if self.entry_price is None:
            return 0
        return (price - self.entry_price) * self.size

    def notional_value(self, price: float) -> float:
        return abs(price * self.size)