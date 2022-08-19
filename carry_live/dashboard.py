import importer
import streamlit as st
from common import util
import config
from ftx_connector import FtxConnectorRest
from common.FtxClientWs import FtxWebsocketClient
from types_ import Cache, WsTicker, TickerCombo
import time
import pandas as pd
import numpy as np

ws_client = FtxWebsocketClient()
connector_rest = FtxConnectorRest(config.API_KEY, config.API_SECRET, config.SUB_ACCOUNT)

EXPIRY = '0930'

MODES = ('Market Overview', 'Positions', 'Open Orders')

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

    if mode == MODES[0]:
        show_market_overview()
    elif mode == MODES[1]:
        show_positions()
    elif mode == MODES[2]:
        show_open_orders()


def show_market_overview():
    _active_futures = util.get_active_futures_with_expiry()
    _expiry = '0930'
    _coins = [coin for coin in _active_futures[_expiry] if coin not in config.BLACKLIST]

    st.title(MODES[0])

    data_table = st.empty()
    while True:
        market_data = []  # ['Coin', 'Perp Price', 'Fut Price', 'Basis', 'Funding']

        def _get_ticker(market: str):
            res = ws_client.get_ticker(market)
            if len(res) == 0:
                return None
            return WsTicker(res)

        for coin in _coins:
            perp_symbol = util.get_perp_symbol(coin)
            fut_symbol = util.get_future_symbol(coin, _expiry)

            perp_ticker = _get_ticker(perp_symbol)
            fut_ticker = _get_ticker(fut_symbol)

            if perp_ticker is None or fut_ticker is None:
                continue

            perp_price = perp_ticker.mark
            fut_price = fut_ticker.mark

            basis = util.get_basis(perp_price, fut_price)
            funding = None  # util.get_funding_rate_avg_24h(perp_symbol)  # todo cache this

            market_data.append(
                {'Coin': coin, 'Perp Price': perp_price, 'Fut Price': fut_price, 'Basis': basis, 'Funding': funding})

        df = pd.DataFrame(market_data)
        data_table.table(df)

        time.sleep(1)


def show_positions():
    st.title(MODES[1])

    data_table = st.empty()

    while True:
        data = []

        for coin in config.WHITELIST:
            cache_path = f'{config.CACHE_FOLDER}/{coin}.json'
            if not util.file_exists(cache_path):
                continue

            cache = Cache()
            cache.read(cache_path)
            if cache.perp_size or cache.fut_size:
                data.append(cache.get_dict())

        df = pd.DataFrame(data)
        df.columns = ['Coin', 'LOB', 'COT', 'Perp Size', 'Fut Size', 'Basis', 'Adj Basis', 'Funding']
        # df.drop(['Perp Price', 'Fut Price'], axis=1, inplace=True)
        # df = df.reindex(['Coin', 'Perp Size', 'Fut Size', 'Basis', 'Funding'], axis=1)
        data_table.table(df)

        time.sleep(1)


def show_open_orders():
    st.title(MODES[2])

    if st.button('Cancel open orders'):
        connector_rest.cancel_orders()


main()
