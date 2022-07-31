import json

API_KEY: str
API_SECRET: str
ACCOUNT: str


with open('config.json') as f:
    data = json.load(f)
    API_KEY = data['api_key']
    API_SECRET = data['api_secret']
    ACCOUNT = data['account']
