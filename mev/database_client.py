import sqlite3


class DatabaseClient:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)

    def _get_pools(self):
        cur = self.conn.cursor()
        cur.execute(f'SELECT * FROM pools;')
        return cur.fetchall()

    def _get_tokens(self):
        cur = self.conn.cursor()
        cur.execute(f'SELECT * FROM tokens;')
        return cur.fetchall()

    def get_pools(self):
        return {i[0].lower(): (i[1].lower(), i[2].lower(), i[3]) for i in self._get_pools()}

    def get_pool_to_exchange_dict(self):
        return {i[0].lower(): i[3] for i in self._get_pools()}

    def get_pair_to_pools_dict(self, min_pools=1, max_pools=3):
        assert min_pools <= max_pools, "min_pools cannot be greater than max_pools"

        pair_to_pools_dict = {}  # {frozenset[token0, token1]: [pools...]}
        for row in self._get_pools():
            pool, token0, token1, _ = row
            pair = frozenset[token0, token1]

            if pair in pair_to_pools_dict:
                pair_to_pools_dict[pair].append(pool)
            else:
                pair_to_pools_dict[pair] = [pool]

        return {pair: pools for pair, pools in pair_to_pools_dict.items() if min_pools <= len(pools) <= max_pools}

    def get_tokens_info(self):
        return {
            i[0].lower(): {'symbol': i[1], 'name': i[2], 'decimals': i[3], 'verified': i[4]}
            for i in self._get_tokens()
        }


if __name__ == '__main__':
    db_client = DatabaseClient('./avalanche.db')
    res = db_client.get_pair_to_pools_dict(2, 3)
    print(res)
