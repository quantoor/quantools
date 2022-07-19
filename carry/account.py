from common.trading import Position
from common.util import logger
import pandas as pd
from results import CarryResults

TRADE_AMOUNT = 100000  # usd
CLOSE_THRESHOLD = 0.1  # %
INIT_OPEN_THRESHOLD = 1.  # %


class Account:
    def __init__(self, coin: str, expiration: str):
        self.spot_position = Position()
        self.perp_position = Position()
        self.fut_position = Position()
        self.tot_profit = 0.

        self.spot_price = 0.
        self.perp_price = 0.
        self.fut_price = 0.
        self.basis = 0.
        self.date = None

        self.trades_open = {}  # {date: basis}
        self.trades_close = {}  # {date: basis}

        self.last_open_basis = 0.
        self.current_open_threshold = INIT_OPEN_THRESHOLD

        self.funding_rate = 0.
        self.funding_paid = 0.
        self.cum_funding_paid = 0.

        self.results = CarryResults(coin, expiration)

    def __str__(self):
        return f'Total profit: {round(self.tot_profit, 2)}'

    def is_trade_on(self) -> bool:
        return self.perp_position.size != 0 or self.fut_position.size != 0

    def next(self, date: str, spot_price: float, perp_price: float, fut_price: float, funding_rate: float):
        self.date = date
        self.spot_price = spot_price
        self.perp_price = perp_price
        self.fut_price = fut_price
        self.basis = (spot_price - fut_price) / spot_price * 100

        # check if there is a trade to close
        if self.is_trade_on() and abs(self.basis) < CLOSE_THRESHOLD:
            self.close_trade()

        elif self.is_trade_on() and abs(self.basis - self.last_open_basis) > 5:
            self.close_trade()
            self.last_open_basis = 0
            self.current_open_threshold = self.basis + 1

        # check if there is a trade to open
        elif abs(self.basis) >= self.current_open_threshold:
            self.open_trade()
            self.current_open_threshold = max(self.current_open_threshold + 1., self.basis)
            self.last_open_basis = self.basis

        # compute funding
        self.funding_rate = funding_rate
        self.funding_paid = funding_rate * self.perp_position.size * self.perp_price
        self.cum_funding_paid += self.funding_paid

        self.update_results()

    def update_results(self):
        self.results.append_results_list({
            'Date': self.date,
            'SpotPrice': self.spot_price,
            'SpotPosSize': self.spot_position.size,
            'SpotPosEntryPrice': self.spot_position.entry_price,
            'PerpPrice': self.perp_price,
            'PerpPosSize': self.perp_position.size,
            'PerpPosEntryPrice': self.perp_position.entry_price,
            'PerpPosPnl': self.perp_position.get_pnl(self.perp_price),
            'FutPrice': self.fut_price,
            'FutPosSize': self.fut_position.size,
            'FutPosEntryPrice': self.fut_position.entry_price,
            'FutPosPnl': self.fut_position.get_pnl(self.fut_price),
            'Basis': self.basis,
            'TradeOpen': True if (self.date in self.trades_open) else False,
            'TradeClose': True if (self.date in self.trades_close) else False,
            'Pnl': self.get_tot_pnl(self.perp_price, self.fut_price),
            'Equity': self.get_equity(self.perp_price, self.fut_price),
            'FundingRate': self.funding_rate,
            'FundingPaid': self.funding_paid,
            'CumFundingPaid': self.cum_funding_paid,
        })

    def open_trade(self):
        spot_amount = TRADE_AMOUNT / self.spot_price
        perp_amount = TRADE_AMOUNT / self.perp_price

        if self.basis > 0:
            # sell perp, buy futures
            self.perp_position.update(self.perp_price, -perp_amount)
            fut_amount = perp_amount
            self.fut_position.update(self.fut_price, fut_amount)
        else:
            # buy spot, sell futures
            self.spot_position.update(self.spot_price, spot_amount)
            fut_amount = spot_amount
            self.fut_position.update(self.fut_price, -fut_amount)

        self.trades_open[self.date] = self.basis

    def close_trade(self):
        profit = self.perp_position.get_pnl(self.perp_price) + self.fut_position.get_pnl(self.fut_price)
        self.tot_profit += profit
        self.perp_position.reset()
        self.fut_position.reset()
        self.current_open_threshold = INIT_OPEN_THRESHOLD

        self.trades_close[self.date] = self.basis
        logger.debug(f'Profit: {round(profit, 2)}')

    def get_tot_pnl(self, perp_price: float, fut_price: float) -> float:
        return self.perp_position.get_pnl(perp_price) + self.fut_position.get_pnl(fut_price)

    def get_equity(self, perp_price: float, fut_price: float) -> float:
        return self.tot_profit + self.get_tot_pnl(perp_price, fut_price) - self.cum_funding_paid

    def get_net_profit(self) -> float:
        return self.tot_profit - self.cum_funding_paid

    def get_results(self) -> pd.DataFrame:
        return self.results.get_df()

    def save_results(self, path: str):
        self.results.write_to_file(path)
