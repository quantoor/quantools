import telegram
import config
import time
import logging


_level_dict = {
    logging.INFO: 'INFO',
    logging.WARNING: 'WARNING',
    logging.ERROR: 'ERROR'
}


class CarryTelegramBot:
    def __init__(self):
        self._chat_id = config.TELEGRAM_CHAT_ID
        self._bot = telegram.Bot(token=config.TELEGRAM_TOKEN)
        self._msg_cache = {}

    def send(self, msg: str, level) -> None:
        if self._enough_time_passed(msg):
            msg = f'[{_level_dict[level]}] {msg}'
            self._bot.sendMessage(chat_id=self._chat_id, text=msg)

    def _enough_time_passed(self, msg: str) -> bool:
        """Avoid sending the same message to frequently"""
        if msg not in self._msg_cache:
            self._msg_cache[msg] = time.time()
            return True
        else:
            last_time_sent = self._msg_cache[msg]
            time_now = time.time()
            enough_time_passed = (time_now - last_time_sent) > 600
            if enough_time_passed:
                self._msg_cache[msg] = time_now
            return enough_time_passed


tg_bot = CarryTelegramBot()
