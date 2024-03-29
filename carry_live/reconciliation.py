from ftx_connector import FtxConnectorRest
import config as cfg
from db_client import DbClient
from common import util

ftx_client = FtxConnectorRest(cfg.API_KEY, cfg.API_SECRET, cfg.SUB_ACCOUNT)
db_client = DbClient('./db/30SEP22.db')


def dump_trades_raw():
    active_futures = util.get_active_futures_with_expiry()
    expiration = '0930'
    coins = [coin for coin in active_futures[expiration]]

    for coin in coins:
        print(coin)

        for trade in ftx_client.get_trades(util.get_perp_symbol(coin)):
            db_client.insert_trade_raw(trade)

        for trade in ftx_client.get_trades(util.get_future_symbol(coin, expiration)):
            db_client.insert_trade_raw(trade)


def dump_positions():
    for position in ftx_client.get_positions():
        print(position.symbol)
        db_client.insert_position(position)


def reconciliate_trades():
    db_client.insert_trades()


# dump_trades_raw()
# dump_positions()
reconciliate_trades()

print('done')
