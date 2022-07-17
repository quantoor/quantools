import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt


class CarryResults:
    def __init__(self, coin: str, expiration: str):
        self.coin = coin
        self.expiration = expiration
        self.results_list = list()
        self.df = None

    def append_results_list(self, results_dict):
        self.results_list.append(results_dict)

    def get_df(self) -> pd.DataFrame:
        if self.df is None:
            self.df = pd.DataFrame(self.results_list)
            # df['Timestamp'] = [dt.datetime.fromtimestamp(ts) for ts in df['Date']]  # add a column with a date format
            # df.set_index('Timestamp', inplace=True)
        return self.df

    def get_final_equity(self) -> float:
        if len(self.results_list) == 0:
            raise Exception('Results list is empty')
        return self.results_list[-1]['Equity']

    def read_from_file(self, path: str):
        self.df = pd.read_csv(path, parse_dates=['Date'])  # , index_col='Date')
        self.results_list = self.df.to_dict('records')
        for i in self.results_list:  # todo remove this
            i.pop('Unnamed: 0', None)

    def write_to_file(self, path: str):
        self.df = self.get_df()
        self.df.to_csv(path, index_label=False)

    def get_figure(self, path) -> matplotlib.figure:
        df = pd.read_csv(path, parse_dates=['Date'])

        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 6), sharex='col')
        fig.suptitle(f'{self.coin} - {self.expiration}')

        dates = df['Date']
        perp_prices = df['PerpPrice']
        fut_prices = df['FutPrice']
        basis = df['Basis']
        trades_open_dict = {date: basis for date, basis, trade_open in zip(df['Date'], df['Basis'], df['TradeOpen'])
                            if trade_open}
        trades_close_dict = {date: basis for date, basis, trade_close in
                             zip(df['Date'], df['Basis'], df['TradeClose']) if trade_close}
        pnl = df['Pnl']
        equity = df['Equity']
        funding_rate = df['FundingRate']
        funding_paid = df['FundingPaid']

        # ax1
        ax1.plot(dates, perp_prices, linewidth=1)
        ax1.plot(dates, fut_prices, linewidth=1)
        ax1.legend(['perp', 'fut'])
        ax1.set_ylabel('Price $', labelpad=10)
        ax1.grid()

        # ax2
        ax2.plot(dates, basis, linewidth=1)  # plot basis
        ax2.plot(trades_open_dict.keys(), trades_open_dict.values(), 'ro', mfc='none')  # plot open trades
        ax2.plot(trades_close_dict.keys(), trades_close_dict.values(), 'rx')  # plot close trades
        ax2.legend(['basis', 'open', 'close'])
        ax2.set_ylabel('Basis %')
        ax2.grid()

        # ax3
        lns1 = ax3.plot(dates, equity, linewidth=1, label='equity')
        # ax3.legend(['equity'])
        ax3.set_ylabel('Equity $', labelpad=10)
        ax3.grid()

        ax3_ = ax3.twinx()
        lns2 = ax3_.plot(dates, pnl, color='orange', linewidth=0.3, label='pnl')
        ax3_.set_ylabel('Pnl $', labelpad=10)

        lns = lns1 + lns2
        labs = [label.get_label() for label in lns]
        ax3.legend(lns, labs)

        # ax4
        lns1 = ax4.plot(dates, funding_paid, linewidth=1, label='funding paid')
        # ax4.fill_between(dates, 0, funding_paid, alpha=0.5, where=funding_paid > 0, facecolor='r')
        # ax4.fill_between(dates, 0, funding_paid, alpha=0.5, where=funding_paid < 0, facecolor='g')
        # ax4.legend(['funding rate', 'funding paid'])
        ax4.set_ylabel('Funding paid $', labelpad=10)
        ax4.grid()

        ax4_ = ax4.twinx()
        lns2 = ax4_.plot(dates, funding_rate * 100, color='orange', linewidth=0.3, label='funding rate')
        ax4_.set_ylabel('Funding rate %', labelpad=10)

        lns = lns1 + lns2
        labs = [label.get_label() for label in lns]
        ax4.legend(lns, labs)

        fig.autofmt_xdate()
        fig.tight_layout()
        return fig

    def check_integrity(self):
        if self.df is None:
            raise Exception('Empty results')
        df = self.df

        for i in range(1, len(df.index)):
            line = i + 1
            date, date_ = df['Date'][i], df['Date'][i - 1]
            perp_price, perp_price_ = df['PerpPrice'][i], df['PerpPrice'][i - 1]
            perp_pos_size, perp_pos_size_ = df['PerpPosSize'][i], df['PerpPosSize'][i - 1]
            perp_pos_entry_price, perp_pos_entry_price_ = df['PerpPosEntryPrice'][i], df['PerpPosEntryPrice'][i - 1]
            perp_pos_pnl, perp_pos_pnl_ = df['PerpPosPnl'][i], df['PerpPosPnl'][i - 1]
            fut_price, fut_price_ = df['FutPrice'][i], df['FutPrice'][i - 1]
            fut_pos_size, fut_pos_size_ = df['FutPosSize'][i], df['FutPosSize'][i - 1]
            fut_pos_entry_price, fut_pos_entry_price_ = df['FutPosEntryPrice'][i], df['FutPosEntryPrice'][i - 1]
            fut_pos_pnl, fut_pos_pnl_ = df['FutPosPnl'][i], df['FutPosPnl'][i - 1]
            basis, basis_ = df['Basis'][i], df['Basis'][i - 1]
            trade_open = df['TradeOpen'][i]
            trade_close = df['TradeClose'][i]
            pnl, pnl_ = df['Pnl'][i], df['Pnl'][i - 1]
            equity, equity_ = df['Equity'][i], df['Equity'][i - 1]
            funding_rate, funding_rate_ = df['FundingRate'][i], df['FundingRate'][i - 1]
            funding_paid, funding_paid_ = df['FundingPaid'][i], df['FundingPaid'][i - 1]
            cum_funding_paid, cum_funding_paid_ = df['CumFundingPaid'][i], df['CumFundingPaid'][i - 1]

            assert not (trade_open and trade_close)
            if trade_open:
                pass
            elif trade_close:
                pass
            else:
                # position size and entry prices did not change
                np.testing.assert_equal(perp_pos_size, perp_pos_size_)
                np.testing.assert_equal(perp_pos_entry_price, perp_pos_entry_price_)
                np.testing.assert_equal(fut_pos_size, fut_pos_size_)
                np.testing.assert_equal(fut_pos_entry_price, fut_pos_entry_price_)

                # check
                d_perp_price = perp_price - perp_price_
                d_perp_pos_pnl = perp_pos_pnl - perp_pos_pnl_
                np.testing.assert_almost_equal(d_perp_price * perp_pos_size, d_perp_pos_pnl)

                d_fut_price = fut_price - fut_price_
                d_fut_pos_pnl = fut_pos_pnl - fut_pos_pnl_
                np.testing.assert_almost_equal(d_fut_price * fut_pos_size, d_fut_pos_pnl)

                # pnl & equity
                d_pnl = pnl - pnl_
                np.testing.assert_almost_equal(perp_pos_pnl + fut_pos_pnl, pnl, err_msg=f'at line {line}')
                np.testing.assert_almost_equal(equity_ + d_pnl - funding_paid, equity, err_msg=f'at line {line}')

                # funding rate paid
                np.testing.assert_almost_equal(perp_pos_size * funding_rate * perp_price, funding_paid)

                # cumulative funding rate paid
                np.testing.assert_almost_equal(cum_funding_paid_ + funding_paid, cum_funding_paid)
