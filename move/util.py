from common import util


def get_expired_move_symbols():
    res = util.client.get_expired_futures()
    return [i['name'] for i in res if i['type'] == 'move']
