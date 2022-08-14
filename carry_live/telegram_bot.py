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
        time_now = time.time()
        keys_to_delete = [key for key, sent_time in self._msg_cache.items() if (time_now - sent_time) > 1800]
        for key in keys_to_delete:
            del self._msg_cache[key]

        if msg in self._msg_cache:
            return False
        else:
            self._msg_cache[msg] = time_now
            return True


tg_bot = CarryTelegramBot()
