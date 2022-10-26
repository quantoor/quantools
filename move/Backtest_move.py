from Volatility import *
from Greeks import *
from main import *



class BackTestMove():
    '''
    backtesting considering the price only,
    columns must include the following :
    position: float
    timestamp: date
    '''

    def __init__(self,max_holding):

        # vertical barrier variable
        self.max_holding = max_holding
        self.max_holding_limit = max_holding

        # Data input
        # self.df = dataframe
        # self.strat_dict = strat_def_dict
        # self.vol_params = deepcopy(vol_params_dict)

        # trade variables
        self.open_pos = False
        self.entry_price = None
        self.direction = None
        self.target_price = None
        self.stop_price = None

        # barrier multipliers
        # closing if one of the TP or SL is hit
        '5% TP and SL'
        self.ub_mult = 1.20
        self.lb_mult = 0.90

        # last date to trade ( closing the trade)
        self.end_date = self.df.timestamp.values[-1]

        self.returns_series = []
        self.hedging_series = []
        self.hedging_pnl_series = []
        self.delta_position_series = []

        # Hedging rule init
        underlying_value_0 = self.df['underlying_price'].iloc[0]

        # rolling cost
        self.rolling_expiry_cost_series = []
        self.rolling_moneyness_cost_series = []

        # winning/losing trades
        self.winning_trades = 0
        self.losing_trades = 0
        self.pnl_from_losing = 0
        self.pnl_from_winning = 0

        self.winning_trades_index = []
        self.losing_trades_index = []
        self.trades_pnl = []

        # cost
        self.cost_from_rolling_moneyness = 0
        self.cost_from_rolling_expiry = 0

        super().__init__([underlying_value_0,underlying_value_0])

        self.store_trades_done = []

    def open_long(self, price):
        '''
        :param price: price we open long at
        :return: populates trade variables from constructor with relevant variables
        '''
        self.open_pos = True
        self.direction = 1
        self.entry_price = price

        if (price > 0):
            self.target_price = price * self.ub_mult
            self.stop_price = price * self.lb_mult
        else:
            self.target_price = price * self.lb_mult
            self.stop_price = price * self.ub_mult

        self.returns_series.append(0)

    def open_short(self, price):
        '''
        :param price: price we open short at
        :return: populates trade variables from constructor with relevant variables
        '''
        self.open_pos = True
        self.direction = -1
        self.entry_price = price

        if (price > 0):
            self.target_price = price * self.lb_mult
            self.stop_price = price * self.ub_mult
        else:
            self.target_price = price * self.ub_mult
            self.stop_price = price * self.lb_mult

        self.returns_series.append(0)

    def reset_variables(self):
        '''
        resets the variables after we close a trade
        '''
        self.open_pos = False
        self.entry_price = None
        self.direction = None
        self.target_price = None
        self.stop_price = None
        self.max_holding = self.max_holding_limit

    def close_position(self,price,**kwargs):
        '''
        :param price: price we are exiting trade at
        :return: appends the trade pnl to the returns series
        and resets variables
        '''

        pnl = np.sign(self.entry_price) * self.direction * ( price / self.entry_price - 1)
        if (pnl >0):
            self.winning_trades += 1
            self.pnl_from_winning += pnl
        else:
            self.losing_trades += 1
            self.pnl_from_losing += pnl
        self.returns_series.append(pnl)
        self.hedging_series.append(self.hedge_cost)
        self.reset_variables()
        self.reset_hedging()

    def monitor_open_positions(self,price,multiple_tracker,timestamp):
        # check upper horizontal barrier for long positions
        if price >= self.target_price and self.direction == 1:
            self.close_position(price)
            print('TP long',multiple_tracker.price,multiple_tracker.price_inception,self.target_price)
            print(' ')

            self.hedging_pnl_series.append(0)
        # check lower horizontal barrier for long positions
        elif price <= self.stop_price and self.direction == 1:
            self.close_position(price)
            print('SL long',multiple_tracker.price,multiple_tracker.price_inception,self.stop_price)
            print(' ')

            self.hedging_pnl_series.append(0)
        # check lower horizontal barrier for short positions
        elif price <= self.target_price and self.direction == -1:
            self.close_position(price)
            print('TP short',multiple_tracker.price,multiple_tracker.price_inception,self.target_price)
            print(' ')
            self.hedging_pnl_series.append(0)

        # check upper horizontal barrier for short positions
        elif price >= self.stop_price and self.direction == -1:
            self.close_position(price)
            print('SL short',multiple_tracker.price,multiple_tracker.price_inception,self.stop_price)
            print(' ')

            self.hedging_pnl_series.append(0)

        # check special case of vertical barrier
        elif timestamp == self.end_date:
            self.close_position(price)
            print('hit_end',multiple_tracker.price,multiple_tracker.price_inception)
            print(' ')

            self.hedging_pnl_series.append(0)
        # check vertical barrier
        elif self.max_holding <= 0:
            self.close_position(price)
            print('max holding reached', multiple_tracker.price, multiple_tracker.price_inception)
            print(' ')

        # if all above conditions not true, decrement max holding by 1 and append a zero to returns column
        else:
            self.max_holding = self.max_holding - 1
            self.returns_series.append(0)
            # self.Hedging(row)
            self.hedging_series.append(self.hedge_cost)
            self.hedging_pnl_series.append(self.delta_pnl)

    def run_backtest(self,storing = True,**kwargs):
        # signals generated from child class
        self.generate_signals(**kwargs)

        plt.plot(self.df['entry'])
        plt.show()

        end_trades = Look_for_end_trading(self.df)
        begin_trades = Look_for_begin_trading(self.df)
        number_of_trades = len(begin_trades)
        print(f'total number of trades = {number_of_trades}')
        N_trades = number_of_trades
        # plt.plot(self.df['ts_rounded_x'],self.df['entry'])
        # plt.show()
        # loop over dataframe

        print('value in hedge class = ', self.underlying_price)
        i = 1


        for trade in tqdm(range(number_of_trades)):
            print(' ')
            print('trade number =', trade)
            begin =  begin_trades[trade]
            begin_entry = self.df['entry'].iloc[begin]
            end = end_trades[trade]
            print('begin trade',begin,self.df['timestamp'].iloc[begin],self.df['entry'].iloc[begin])
            print('end trade', end,self.df['timestamp'].iloc[end])
            time_left = end - begin + 1
            for row in self.df.iloc[begin:end+1].itertuples():
                # print(f'new_position_for_trade_{trade}')
                time_left -= 1
                # if we get a long signal and do not have open position open a long
                if row.entry == 1 and self.open_pos is False:
                    multiple_tracker = Multiple_trackers(row.timestamp,self.strat_dict, self.vol_params)
                    print('opening long')
                    self.open_long(multiple_tracker.price)
                    underlying_price = multiple_tracker.underlying_price
                    delta = multiple_tracker.greeks['delta']
                    gamma = multiple_tracker.greeks['gamma']
                    self.Hedging(row.timestamp,underlying_price,delta,gamma,hedging_choice='treshold')
                    self.hedging_series.append(self.hedge_cost)
                    self.delta_position_series.append(self.delta_position)
                # if we get a short position and do not have open position open a short
                elif row.entry == -1 and self.open_pos is False:
                    print('opening short')
                    multiple_tracker = Multiple_trackers(row.timestamp, self.strat_dict, self.vol_params)
                    self.open_short(multiple_tracker.price)
                    underlying_price = multiple_tracker.underlying_price
                    delta = multiple_tracker.greeks['delta']
                    gamma = multiple_tracker.greeks['gamma']
                    self.Hedging(row.timestamp, underlying_price, delta, gamma, hedging_choice='treshold')
                    self.hedging_series.append(self.hedge_cost)
                    self.delta_position_series.append(self.delta_position)
                # monitor open positions to see if any of the barriers have been touched
                elif self.open_pos is True:
                    multiple_tracker.update_info(row.timestamp,self.vol_params)
                    self.monitor_open_positions(multiple_tracker.price,multiple_tracker,row.timestamp)
                    underlying_price = multiple_tracker.underlying_price
                    delta = multiple_tracker.greeks['delta']
                    gamma = multiple_tracker.greeks['gamma']
                    self.Hedging(row.timestamp, underlying_price, delta, gamma, hedging_choice='treshold')
                    self.delta_position_series.append(self.delta_position)
                    self.hedging_pnl_series.append(self.delta_pnl)

                    if (self.open_pos is False):
                        self.cost_from_rolling_moneyness += sum(multiple_tracker.rebalance)
                        self.cost_from_rolling_expiry += sum(multiple_tracker.cost_from_rolling)

                        if (self.returns_series[-1] > 0):
                            self.winning_trades_index.append(trade)

                        else:
                            self.losing_trades_index.append(trade)

                        self.trades_pnl.append(self.returns_series[-1])

                        if (storing == True):

                            self.store_trades_done.append(multiple_tracker)

                        print(f'time_left_until_next_trade = {time_left}')
                        for i in range(time_left):
                            self.returns_series.append(0)
                            self.hedging_series.append(0)
                            self.delta_position_series.append(self.delta_position)
                        break
