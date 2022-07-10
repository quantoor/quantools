import streamlit as st
import util
from carry_backtesting import CarryBacktesting
import datetime as dt


def carry_backtesting():
    # instruments
    col1, col2 = st.columns(2)
    with col1:
        coin = st.text_input('Coin', value='AAVE')

    with col2:
        fut_expiration = st.selectbox('Future expiration', ['0624'])

    # dates
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", dt.datetime(2022, 3, 20, 0))

    with col2:
        end_date = st.date_input("End date", dt.datetime(2022, 6, 24, 0))

    start_ts = util.date_to_timestamp(start_date.year, start_date.month, start_date.day, 0)
    end_ts = util.date_to_timestamp(end_date.year, end_date.month, end_date.day, 0)

    # backtesting
    backtester = CarryBacktesting()
    fig = backtester.backtest_carry(coin, fut_expiration, 3600, start_ts, end_ts,
                                    overwrite_results=False)
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
