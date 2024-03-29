import telegram
import config
import time
import logging
from datetime import datetime


_level_dict = {
    logging.INFO: 'INFO',
    logging.WARNING: 'WARNING',
    logging.ERROR: 'ERROR'
}

TG_CAN_OPEN = 'can_open'
TG_CAN_INCREMENT = 'can_increment'
TG_CAN_CLOSE = 'can_close'
TG_REACHED_MAX_POSITIONS = 'reached_max_positions'
TG_ERROR = 'error'
TG_ALWAYS_NOTIFY = 'always_notify'


class TgMsg:
    def __init__(self, coin: str, msg_type: str, msg: str, level: int):
        self.coin = coin
        self.msg_type = msg_type
        self.msg = msg
        self.level = level


class TgBot:
    def __init__(self):
        self._chat_id = config.TELEGRAM_CHAT_ID
        self._bot = telegram.Bot(token=config.TELEGRAM_TOKEN)
        self._msg_cache = {}

    def send(self, tg_msg: TgMsg) -> None:
        if self._enough_time_passed(tg_msg):
            ts = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            msg = f'[{ts}] [{_level_dict[tg_msg.level]}] {tg_msg.msg}'
            self._bot.sendMessage(chat_id=self._chat_id, text=msg)

    def _enough_time_passed(self, msg: TgMsg) -> bool:
        """Avoid sending the same message to frequently"""
        time_now = time.time()
        keys_to_delete = [key for key, sent_time in self._msg_cache.items() if (time_now - sent_time) > 1800]
        for key in keys_to_delete:
            del self._msg_cache[key]

        key = msg.coin + msg.msg_type
        if key in self._msg_cache:
            return False
        else:
            self._msg_cache[key] = time_now
            return True


tg_bot = TgBot()
