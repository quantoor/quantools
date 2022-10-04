import json


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

    REFRESH_TIME: int = data['refresh_time']
