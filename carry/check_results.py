from results import CarryResults
from common import util
import config
from common.util import logger

results_folders = util.get_folders_in_folder(f'{config.RESULTS_FOLDER}')

for folder in results_folders:

    results_files = util.get_files_in_folder(folder.name, '.csv')

    for file in results_files:

        logger.info(f'{folder.name}/{file.name}')
        r = CarryResults(file.name, folder.name)
        r.read_from_file(f'./{config.RESULTS_FOLDER}/{folder.name}/{file.name}')
        r.check_integrity()
