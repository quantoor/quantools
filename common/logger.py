import logging
from datetime import datetime


class Logger:
    def __init__(self):
        self._logger = logging.getLogger("Log")
        self._logger.setLevel(logging.DEBUG)
        self._formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')

    def add_console(self, level=logging.DEBUG):
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(self._formatter)
        self._logger.addHandler(ch)

    def add_file(self, log_folder: str, level=logging.INFO):
        ts = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
        fh = logging.FileHandler(f'{log_folder}/{ts}.log')
        fh.setLevel(level)
        fh.setFormatter(self._formatter)
        self._logger.addHandler(fh)

    def debug(self, msg: str):
        self._logger.debug(msg)

    def info(self, msg: str):
        self._logger.info(msg)

    def warning(self, msg: str):
        self._logger.warning(msg)

    def error(self, msg: str):
        self._logger.error(msg)


logger = Logger()
