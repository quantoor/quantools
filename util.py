import datetime as dt
import logging
from pathlib import Path
import pandas as pd


logger = logging.getLogger("Log")
logger.setLevel(logging.DEBUG)

# console
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def date_to_timestamp(year: int, month: int, day: int, hour: int) -> int:
    date = dt.datetime(year, month, day, hour)
    return int(dt.datetime.timestamp(date))


def timestamp_now() -> int:
    return int(dt.datetime.now().timestamp())


def file_exists(file_path: str) -> bool:
    return Path(file_path).is_file()


def load_results(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
