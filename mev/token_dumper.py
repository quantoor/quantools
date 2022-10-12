from brownie import *
import os
import sqlite3
from classes import Token


SNOWTRACE_API_KEY = "JCGRVAFIADSVISFU675XCRNRNKII4Z7UBJ"
os.environ["SNOWTRACE_TOKEN"] = SNOWTRACE_API_KEY

network.connect('avax-main-quicknode-ws')

DB_NAME = './pools.db'


def get_pools(table):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM {table};')
    return [(x[0].lower(), x[1].lower(), x[2].lower()) for x in cur.fetchall()]


def create_token_table():
    conn = sqlite3.connect(DB_NAME)
    query = f'''CREATE TABLE IF NOT EXISTS tokens (
            address TEXT NOT NULL PRIMARY KEY,
            symbol TEXT,
            name TEXT,
            decimals INT,
            verified BOOL NOT NULL);
            '''
    conn.execute(query)


def get_tokens(only_address=True):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM tokens;')

    if only_address:
        return [x[0] for x in cur.fetchall()]
    else:
        return cur.fetchall()


def insert_token(token: Token):
    conn = sqlite3.connect(DB_NAME)
    if token.verified:
        query = f'''
                INSERT INTO tokens (address, symbol, name, decimals, verified)
                VALUES ('{token.address}', '{token.symbol}', '{token.name}', {token.decimals}, {token.verified});
                '''
    else:
        query = f'''
                INSERT INTO tokens (address, verified)
                VALUES ('{token.address}', {token.verified});
                '''
    try:
        conn.execute(query)
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    except Exception as e:
        print(query, e)


def main():
    create_token_table()

    all_token_addresses = set()
    for _table in ['sushiswap_pools', 'traderjoe_pools', 'pangolin_pools']:
        for pool in get_pools(_table):
            all_token_addresses.add(pool[1])
            all_token_addresses.add(pool[2])
    all_token_addresses = list(all_token_addresses)

    for i, token_address in enumerate(all_token_addresses):
        print(f'Storing token {i}/{len(all_token_addresses)}')

        if token_address not in get_tokens():
            insert_token(Token().from_explorer(token_address))


main()
