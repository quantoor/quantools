import sqlite3


class DatabaseClient:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)

    def _get_pools(self, table):
        cur = self.conn.cursor()
        cur.execute(f'SELECT * FROM {table};')
        return cur.fetchall()

    def _get_tokens(self):
        cur = self.conn.cursor()
        cur.execute(f'SELECT * FROM tokens;')
        return cur.fetchall()

    def get_pool_to_pair_dict(self, table):
        return {i[0]: (i[1], i[2]) for i in self._get_pools(table)}

    def get_tokens_info(self):
        return {i[0]: {'symbol': i[1], 'name': i[2], 'decimals': i[3], 'verified': i[4]} for i in self._get_tokens()}


if __name__ == '__main__':
    db_client = DatabaseClient('./pools.db')
    pools = db_client.get_pool_to_pair_dict('pangolin_pools')
    tokens = db_client.get_tokens_info()
