from ftx_connector import FtxConnectorRest
import config as cfg
from db_client import DbClient
from common import util

ftx_client = FtxConnectorRest(cfg.API_KEY, cfg.API_SECRET, cfg.SUB_ACCOUNT)
db_client = DbClient('./db/30SEP22.db')

active_futures = util.get_active_futures_with_expiry()
expiration = '0930'
coins = [coin for coin in active_futures[expiration]]

for coin in coins:
    print(coin)

    for trade in ftx_client.get_trades(util.get_perp_symbol(coin)):
        db_client.insert_trade(trade)

    for trade in ftx_client.get_trades(util.get_future_symbol(coin, expiration)):
        db_client.insert_trade(trade)

print('done')
