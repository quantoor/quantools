import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import streamlit as st
from common import util
import config
from ftx_connector_rest import FtxConnectorRest
from types_ import Cache
import time
import pandas as pd
import numpy as np

ACTIVE_FUTURES = util.get_active_futures_with_expiry()
EXPIRY = '0930'
COINS = [coin for coin in ACTIVE_FUTURES[EXPIRY] if coin not in config.BLACKLIST]

if st.button('Cancel open orders'):
    connector_rest = FtxConnectorRest(config.API_KEY, config.API_SECRET, config.SUB_ACCOUNT)
    connector_rest.cancel_orders()

st.header('Active coins:')
st.subheader(COINS)

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
    df.columns = ['Coin', 'LOB', 'COT', 'Perp Price', 'Perp Size', 'Fut Price', 'Fut Size', 'Basis']
    data_table.table(df)

    time.sleep(config.REFRESH_TIME)
