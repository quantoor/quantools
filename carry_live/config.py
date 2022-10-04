from typing import List
import json
from firestore_client import FirestoreClient


with open('./config.json') as f:
    data = json.load(f)

    CACHE_FOLDER: str = data['cache_folder']
    LOG_FOLDER: str = data['log_folder']

    ftx = data['ftx']
    API_KEY: str = ftx['api_key']
    API_SECRET: str = ftx['api_secret']
    SUB_ACCOUNT: str = ftx['sub_account']

    telegram = data['telegram']
    TELEGRAM_TOKEN: str = telegram['token']
    TELEGRAM_CHAT_ID: int = telegram['chat_id']

    settings = FirestoreClient().get_strategy_settings()
    BLACKLIST: List[str] = settings['blacklist']
    WHITELIST: List[str] = settings['whitelist']
    EXPIRY: str = settings['expiration']
    REFRESH_TIME: int = settings['refresh_time']
    TRADE_SIZE_USD: float = settings['trade_size_usd']
    THRESHOLD_INCREMENT: float = settings['threshold_increment']
    MAX_N_POSITIONS: int = settings['max_n_positions']
    SPREAD_OFFSET: float = settings['spread_offset']
