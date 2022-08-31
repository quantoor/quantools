import importer
import streamlit as st
from common import util
import config
from ftx_connector import FtxConnectorRest
from common.FtxClientWs import FtxWebsocketClient
from classes import StrategyCache, WsTicker
import time
import pandas as pd
import asyncio
from classes import TickerCombo

ws_client = FtxWebsocketClient()
connector_rest = FtxConnectorRest(config.API_KEY, config.API_SECRET, config.SUB_ACCOUNT)

EXPIRY = '0930'

MODES = ('Market Overview', 'Positions', 'Manual Trading')

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
        MODES[2]: lambda: show_manual_trading()
    }

    modes[mode]()


_active_futures = util.get_active_futures_with_expiry()
_expiry = '0930'
_coins = [coin for coin in _active_futures[_expiry] if coin not in config.BLACKLIST]
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

            perp_price = perp_ticker.mark
            fut_price = fut_ticker.mark

            basis = util.get_basis(perp_price, fut_price)

            if abs(basis) > 1:
                market_data.append({
                    'Coin': coin,
                    'Perp Price': perp_price,
                    'Fut Price': fut_price,
                    'Basis': basis,
                    'Funding': None,  # util.get_funding_rate_avg_24h(perp_symbol)
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

        for coin in config.WHITELIST:
            cache_path = f'{config.CACHE_FOLDER}/{coin}.json'
            if not util.file_exists(cache_path):
                continue

            cache = StrategyCache()
            cache.read(cache_path)
            if cache.perp_size or cache.fut_size:
                data.append(cache.to_dict())

        df = pd.DataFrame(data)
        df.columns = ['Coin', 'LOB', 'COT', 'Perp Size', 'Fut Size', 'Basis', 'Adj Basis Open', 'Adj Basis Close',
                      'Funding']
        # df.drop(['Perp Price', 'Fut Price'], axis=1, inplace=True)
        # df = df.reindex(['Coin', 'Perp Size', 'Fut Size', 'Basis', 'Funding'], axis=1)
        data_table.table(df)

        time.sleep(1)


def show_manual_trading():
    st.title(MODES[2])

    offset = st.number_input('Spread offset', min_value=0., max_value=2., value=1.2)

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

        size = 50 / max(perp_ticker.mark, fut_ticker.mark)

        if ticker_combo.is_contango:
            # buy perp, sell future
            connector_rest.place_order_limit(perp_symbol, True, perp_ticker.bid / offset, size)
            connector_rest.place_order_limit(fut_symbol, False, fut_ticker.ask * offset, size)
        else:
            # buy future, sell perp
            connector_rest.place_order_limit(fut_symbol, True, fut_ticker.bid / offset, size)
            connector_rest.place_order_limit(perp_symbol, False, perp_ticker.ask * offset, size)


main()
