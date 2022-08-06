from common.trading import Position
from common.util import logger
import pandas as pd
from results import CarryResults

TRADE_AMOUNT = 100000  # usd
CLOSE_THRESHOLD = 0.1  # %
INIT_OPEN_THRESHOLD = 1.  # %


class Account:
    def __init__(self, coin: str, expiration: str):
        self._spot_position = Position()
        self._perp_position = Position()
        self._fut_position = Position()
        self._tot_profit = 0.

        self._spot_price = 0.
        self._perp_price = 0.
        self._fut_price = 0.
        self._basis = 0.
        self._date = None

        self._trades_open = {}  # {date: basis}
        self._trades_close = {}  # {date: basis}

        self._last_open_basis = 0.
        self._current_open_threshold = INIT_OPEN_THRESHOLD

        self._funding_rate = 0.
        self._funding_paid = 0.
        self._cum_funding_paid = 0.

        self.results = CarryResults(coin, expiration)

    def __str__(self):
        return f'Total profit: {round(self._tot_profit, 2)}'

    def is_trade_on(self) -> bool:
        return self._perp_position.size != 0 or self._fut_position.size != 0

    def next(self, date: str, spot_price: float, perp_price: float, fut_price: float, funding_rate: float) -> None:
        self._date = date
        self._spot_price = spot_price
        self._perp_price = perp_price
        self._fut_price = fut_price
        self._basis = (perp_price - fut_price) / perp_price * 100  # todo spot price

        # check if there is a trade to close
        if self.is_trade_on() and abs(self._basis) < CLOSE_THRESHOLD:
            self.close_trade()

        elif self.is_trade_on() and abs(self._basis - self._last_open_basis) > 5:
            self.close_trade()
            self._last_open_basis = 0
            self._current_open_threshold = abs(self._basis) + 1

        # check if there is a trade to open
        elif abs(self._basis) >= self._current_open_threshold:
            self.open_trade()
            self._current_open_threshold = max(self._current_open_threshold + 1., abs(self._basis))
            self._last_open_basis = abs(self._basis)

        # compute funding
        self._funding_rate = funding_rate
        self._funding_paid = funding_rate * self._perp_position.size * self._perp_price
        self._cum_funding_paid += self._funding_paid

        self.update_results()

    def update_results(self) -> None:
        self.results.append_results_list({
            'Date': self._date,
            'SpotPrice': self._spot_price,
            'SpotPosSize': self._spot_position.size,
            'SpotPosEntryPrice': self._spot_position.entry_price,
            'PerpPrice': self._perp_price,
            'PerpPosSize': self._perp_position.size,
            'PerpPosEntryPrice': self._perp_position.entry_price,
            'PerpPosPnl': self._perp_position.get_pnl(self._perp_price),
            'FutPrice': self._fut_price,
            'FutPosSize': self._fut_position.size,
            'FutPosEntryPrice': self._fut_position.entry_price,
            'FutPosPnl': self._fut_position.get_pnl(self._fut_price),
            'Basis': self._basis,
            'TradeOpen': True if (self._date in self._trades_open) else False,
            'TradeClose': True if (self._date in self._trades_close) else False,
            'Pnl': self.get_tot_pnl(self._perp_price, self._fut_price),
            'Equity': self.get_equity(self._perp_price, self._fut_price),
            'FundingRate': self._funding_rate,
            'FundingPaid': self._funding_paid,
            'CumFundingPaid': self._cum_funding_paid,
        })

    def open_trade(self) -> None:
        # todo buy spot if in contango
        # spot_amount = TRADE_AMOUNT / self.spot_price
        perp_amount = TRADE_AMOUNT / self._perp_price

        if self._basis > 0:
            # sell perp, buy futures
            self._perp_position.update(self._perp_price, -perp_amount)
            fut_amount = perp_amount
            self._fut_position.update(self._fut_price, fut_amount)
        else:
            # buy perp, sell futures
            self._perp_position.update(self._perp_price, perp_amount)
            fut_amount = perp_amount
            self._fut_position.update(self._fut_price, -fut_amount)

        self._trades_open[self._date] = self._basis

    def close_trade(self) -> None:
        profit = self._perp_position.get_pnl(self._perp_price) + self._fut_position.get_pnl(self._fut_price)
        self._tot_profit += profit
        self._perp_position.reset()
        self._fut_position.reset()
        self._current_open_threshold = INIT_OPEN_THRESHOLD

        self._trades_close[self._date] = self._basis
        logger.debug(f'Profit: {round(profit, 2)}')

    def get_tot_pnl(self, perp_price: float, fut_price: float) -> float:
        return self._perp_position.get_pnl(perp_price) + self._fut_position.get_pnl(fut_price)

    def get_equity(self, perp_price: float, fut_price: float) -> float:
        return self._tot_profit + self.get_tot_pnl(perp_price, fut_price) - self._cum_funding_paid

    def get_net_profit(self) -> float:
        return self._tot_profit - self._cum_funding_paid

    def get_results(self) -> pd.DataFrame:
        return self.results.get_df()

    def save_results(self, path: str):
        self.results.write_to_file(path)
