import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import streamlit as st
from common import util
import config
from ftx_connector import FtxConnectorRest
from types_ import Cache
import time
import pandas as pd


ACTIVE_FUTURES = util.get_active_futures_with_expiry()
EXPIRY = '0930'
COINS = [coin for coin in ACTIVE_FUTURES[EXPIRY] if coin not in config.BLACKLIST]

# st.header('Active coins:')
# st.subheader(COINS)
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
    st.title(MODES[0])

    data_table = st.empty()

    while True:
        data = []

        for coin in COINS:
            cache_path = f'{config.CACHE_FOLDER}/{coin}.json'
            if not util.file_exists(cache_path):
                continue

            cache = Cache(cache_path)
            data.append(cache.get_dict())

        df = pd.DataFrame(data)
        df['basis'] = (df['perp_price'] - df['fut_price']) / df['perp_price'] * 100
        df.columns = ['Coin', 'LOB', 'COT', 'Perp Price', 'Perp Size', 'Fut Price', 'Fut Size', 'Funding', 'Basis']
        df.drop(['LOB', 'COT', 'Perp Size', 'Fut Size'], axis=1, inplace=True)
        df = df.reindex(['Coin', 'Perp Price', 'Fut Price', 'Basis', 'Funding'], axis=1)
        data_table.table(df)

        time.sleep(1)


def show_positions():
    st.title(MODES[1])

    data_table = st.empty()

    while True:
        data = []

        for coin in COINS:
            cache_path = f'{config.CACHE_FOLDER}/{coin}.json'
            if not util.file_exists(cache_path):
                continue

            cache = Cache(cache_path)
            if cache.perp_size or cache.fut_size:
                data.append(cache.get_dict())

        df = pd.DataFrame(data)
        df['basis'] = (df['perp_price'] - df['fut_price']) / df['perp_price'] * 100
        df.columns = ['Coin', 'LOB', 'COT', 'Perp Price', 'Perp Size', 'Fut Price', 'Fut Size', 'Funding', 'Basis']
        df.drop(['Perp Price', 'Fut Price'], axis=1, inplace=True)
        df = df.reindex(['Coin', 'Perp Size', 'Fut Size', 'Basis', 'Funding'], axis=1)
        data_table.table(df)

        time.sleep(1)


def show_open_orders():
    st.title(MODES[2])

    if st.button('Cancel open orders'):
        connector_rest = FtxConnectorRest(config.API_KEY, config.API_SECRET, config.SUB_ACCOUNT)
        connector_rest.cancel_orders()


main()
