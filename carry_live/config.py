from typing import List
import json

CACHE_FOLDER: str
LOG_FOLDER: str
API_KEY: str
API_SECRET: str
SUB_ACCOUNT: str
BLACKLIST: List[str]
WHITELIST: List[str]
REFRESH_TIME: float
TRADE_SIZE_USD: float
INIT_OPEN_THRESHOLD: float
THRESHOLD_INCREMENT: float

with open('./config.json') as f:
    data = json.load(f)

    CACHE_FOLDER = data['cache_folder']
    LOG_FOLDER = data['log_folder']
    API_KEY = data['api_key']
    API_SECRET = data['api_secret']
    SUB_ACCOUNT = data['sub_account']
    BLACKLIST = sorted(data['blacklist'])
    WHITELIST = sorted(data['whitelist'])
    REFRESH_TIME = data['refresh_time']

    strategy = data['strategy']
    TRADE_SIZE_USD = strategy['trade_size_usd']
    INIT_OPEN_THRESHOLD = strategy['init_open_threshold']
    THRESHOLD_INCREMENT = strategy['threshold_increment']
