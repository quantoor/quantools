from typing import List
import json

API_KEY: str
API_SECRET: str
SUB_ACCOUNT: str
BLACKLIST: List[str]

with open('./config.json') as f:
    data = json.load(f)
    API_KEY = data['api_key']
    API_SECRET = data['api_secret']
    SUB_ACCOUNT = data['sub_account']
    BLACKLIST = data['blacklist']
