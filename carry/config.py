import json

CACHE_FOLDER: str
RESULTS_FOLDER: str


with open('./config.json') as f:
    data = json.load(f)
    CACHE_FOLDER = data['cache_folder']
    RESULTS_FOLDER = data['results_folder']
