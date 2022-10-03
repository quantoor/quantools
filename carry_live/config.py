from typing import List
import json

CACHE_FOLDER: str
LOG_FOLDER: str
API_KEY: str
API_SECRET: str
SUB_ACCOUNT: str
TELEGRAM_TOKEN: str
TELEGRAM_CHAT_ID: str
BLACKLIST: List[str]
WHITELIST: List[str]
REFRESH_TIME: float
LIVE_TRADE: bool
TRADE_SIZE_USD: float
THRESHOLD_INCREMENT: float
SPREAD_OFFSET: float

with open('./config.json') as f:
    data = json.load(f)

    CACHE_FOLDER = data['cache_folder']
    LOG_FOLDER = data['log_folder']

    ftx = data['ftx']
    API_KEY = ftx['api_key']
    API_SECRET = ftx['api_secret']
    SUB_ACCOUNT = ftx['sub_account']

    telegram = data['telegram']
    TELEGRAM_TOKEN = telegram['token']
    TELEGRAM_CHAT_ID = telegram['chat_id']

    BLACKLIST = sorted(data['blacklist'])
    WHITELIST = sorted(data['whitelist'])
    EXPIRY = data['expiry']
    REFRESH_TIME = data['refresh_time']

    strategy = data['strategy']
    TRADE_SIZE_USD = strategy['trade_size_usd']
    THRESHOLD_INCREMENT = strategy['threshold_increment']
    MAX_N_POSITIONS = strategy['max_n_positions']
    SPREAD_OFFSET = strategy['spread_offset']
