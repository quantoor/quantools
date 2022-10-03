import importer
import config as cfg
from common import util
from common.logger import logger
from bot import CarryBot
from version import __version__

if __name__ == '__main__':
    util.create_folder(cfg.CACHE_FOLDER)
    util.create_folder(cfg.LOG_FOLDER)

    logger.add_console()
    logger.add_file(cfg.LOG_FOLDER)
    logger.info(f'Start CarryBot v{__version__}')

    active_futures = util.get_active_futures_with_expiry()
    coins = [coin for coin in active_futures[cfg.EXPIRY] if coin not in cfg.BLACKLIST]

    bot = CarryBot()
    bot.start(coins, cfg.EXPIRY)
