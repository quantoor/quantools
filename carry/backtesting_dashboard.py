import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import streamlit as st
from common import util
from backtesting import CarryBacktesting


def carry_backtesting():
    # instruments
    col1, col2 = st.columns(2)
    with col1:
        coin = st.selectbox('Coin', util.get_all_futures_coins())

    with col2:
        fut_expiration = st.selectbox('Future expiration', util.get_historical_expirations())

    # backtesting
    backtester = CarryBacktesting()
    backtester.backtest_single(coin, fut_expiration, 3600, use_cache=True, overwrite_results=False)
    fig = backtester.account.results.get_figure()  # todo fix this
    st.pyplot(fig)


with st.sidebar:
    mode = st.radio(
        "Choose Mode",
        ("Carry Backtesting", "Options Analysis")
    )

if mode == 'Carry Backtesting':
    carry_backtesting()
elif mode == 'Options Analysis':
    st.title('TODO')
