import datetime

import importer
import streamlit as st
from common import util
import config as cfg
from ftx_connector import FtxConnectorRest
from common.FtxClientWs import FtxWebsocketClient
from classes import StrategyStatus, WsTicker
import time
import pandas as pd
import asyncio
from classes import TickerCombo
import matplotlib.pyplot as plt


ws_client = FtxWebsocketClient()
connector_rest = FtxConnectorRest(cfg.API_KEY, cfg.API_SECRET, cfg.SUB_ACCOUNT)

EXPIRY = '0930'

MODES = ('Market Overview', 'Positions', 'Manual Trading', 'Funding')

# CSS to inject contained in a string
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """

# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)


def main():
    with st.sidebar:
        mode = st.radio("Mode", MODES)

    modes = {
        MODES[0]: lambda: show_market_overview(),
        MODES[1]: lambda: show_positions(),
        MODES[2]: lambda: show_manual_trading(),
        MODES[3]: lambda: show_funding()
    }

    modes[mode]()


_active_futures = util.get_active_futures_with_expiry()
_expiry = '1230'
_coins = [coin for coin in _active_futures[_expiry] if coin not in cfg.BLACKLIST]
fundings = {coin: None for coin in _coins}


def show_market_overview():
    st.title(MODES[0])
    loop = asyncio.new_event_loop()
    # loop.create_task(_get_funding())
    # loop.create_task(_market_overview())
    # loop.run_forever()
    _market_overview()


async def _get_funding():
    while True:
        for coin in _coins:
            fundings[coin] = util.get_funding_rate_avg_24h(util.get_perp_symbol(coin))
            _ = await asyncio.sleep(0.01)
        _ = await asyncio.sleep(30)


def _get_ticker(market: str):
    res = ws_client.get_ticker(market)
    if len(res) == 0:
        return None
    return WsTicker(res)


def _market_overview():
    data_table = st.empty()
    while True:
        market_data = []  # ['Coin', 'Perp Price', 'Fut Price', 'Basis', 'Funding']

        for coin in _coins:
            perp_symbol = util.get_perp_symbol(coin)
            fut_symbol = util.get_future_symbol(coin, _expiry)

            perp_ticker = _get_ticker(perp_symbol)
            fut_ticker = _get_ticker(fut_symbol)

            if perp_ticker is None or fut_ticker is None:
                continue

            ticker_combo = TickerCombo(coin, _expiry, perp_ticker, fut_ticker)

            # if abs(ticker_combo.adj_basis_open) > 1:
            market_data.append({
                'Coin': coin,
                'Perp Price': perp_ticker.mark,
                'Fut Price': fut_ticker.mark,
                'Basis': ticker_combo.basis,
                # 'Adj Basis Open': ticker_combo.adj_basis_open,
                # 'Funding': None,  # util.get_funding_rate_avg_24h(perp_symbol)
            })

        df = pd.DataFrame(market_data)
        data_table.table(df)

        # _ = await asyncio.sleep(1)
        time.sleep(1)


def show_positions():
    st.title(MODES[1])

    data_table = st.empty()

    while True:
        data = []

        for coin in cfg.WHITELIST:
            cache_path = f'{cfg.CACHE_FOLDER}/{coin}.json'
            if not util.file_exists(cache_path):
                continue

            cache = StrategyStatus()
            cache.read(cache_path)
            if cache.perp_size or cache.fut_size:
                data.append(cache.to_dict())

        df = pd.DataFrame(data)
        df.columns = ['Coin', 'LOB', 'COT', 'Perp Size', 'Fut Size', 'Basis', 'Adj Basis Open', 'Adj Basis Close',
                      'Funding']
        df.drop(['LOB', 'COT'], axis=1, inplace=True)
        df = df.reindex(['Coin', 'Perp Size', 'Fut Size', 'Adj Basis Open', 'Basis', 'Adj Basis Close',
                         'Funding'], axis=1)
        data_table.table(df)

        time.sleep(1)


def show_manual_trading():
    st.title(MODES[2])

    offset = st.number_input('Spread offset', min_value=0., max_value=2., value=1.05)

    coin = st.selectbox('Coin', [""] + _coins)
    if not coin:
        return

    perp_symbol = util.get_perp_symbol(coin)
    fut_symbol = util.get_future_symbol(coin, _expiry)

    basis_placeholder = st.empty()
    basis_placeholder.json({
        "is_contango": None,
        "basis": None,
        "adj_basis_open": None,
        "adj_basis_close": None
    })

    if st.button('Get Tickers'):
        perp_ticker = WsTicker(connector_rest._client.get_future(perp_symbol))
        fut_ticker = WsTicker(connector_rest._client.get_future(fut_symbol))

        ticker_combo = TickerCombo(coin, _expiry, perp_ticker, fut_ticker)
        basis_placeholder.json({
            "is_contango": ticker_combo.is_contango,
            "basis": round(ticker_combo.basis, 4),
            "adj_basis_open": round(ticker_combo.adj_basis_open, 4),
            "adj_basis_close": round(ticker_combo.adj_basis_close, 4)
        })

    if st.button('Open Position'):
        perp_ticker = WsTicker(connector_rest._client.get_future(perp_symbol))
        fut_ticker = WsTicker(connector_rest._client.get_future(fut_symbol))
        ticker_combo = TickerCombo(coin, _expiry, perp_ticker, fut_ticker)

        size = cfg.TRADE_SIZE_USD / max(perp_ticker.mark, fut_ticker.mark)

        if ticker_combo.is_contango:
            # buy perp, sell future
            connector_rest.place_order_limit(perp_symbol, True, perp_ticker.ask / offset, size)
            connector_rest.place_order_limit(fut_symbol, False, fut_ticker.bid * offset, size)
        else:
            # buy future, sell perp
            connector_rest.place_order_limit(fut_symbol, True, fut_ticker.ask / offset, size)
            connector_rest.place_order_limit(perp_symbol, False, perp_ticker.bid * offset, size)


def show_funding():
    st.title(MODES[3])

    perps = [""] + [c + '-PERP' for c in _coins]
    perp = st.selectbox('Perp', perps)
    if not perp:
        return

    n_days = st.number_input('Days', min_value=1, max_value=30, value=7)

    ts = util.timestamp_now()
    ts_vec, fundings_vec = util.get_historical_funding(perp, ts - n_days * 24 * 3600, ts)
    date_vec = [datetime.datetime.fromtimestamp(t).isoformat() for t in ts_vec]
    print(date_vec)
    fundings_annualized_vec = [f * 24 * 365 / 100 for f in fundings_vec]

    fig, ax = plt.subplots()
    ax.plot(date_vec, fundings_annualized_vec)
    ax.set_xticklabels(fundings_annualized_vec, rotation=45, fontsize=8)
    st.pyplot(fig)


main()
