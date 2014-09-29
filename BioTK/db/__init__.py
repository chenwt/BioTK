import os
import functools
import pickle

import pandas as pd
import psycopg2.pool

from BioTK import CONFIG

DECIMAL_TO_FLOAT = psycopg2.extensions.new_type(
        psycopg2.extensions.DECIMAL.values,
        'DECIMAL_TO_FLOAT',
        lambda value, curs: float(value) if value is not None else None)
psycopg2.extensions.register_type(DECIMAL_TO_FLOAT)

pool = None

def connect():
    global pool
    if pool is None:
        pool = psycopg2.pool.ThreadedConnectionPool(
            1, 100,
            database=CONFIG["db.name"],
            user=CONFIG["db.user"],
            host=CONFIG["db.host"],
            port=int(CONFIG["db.port"]))
    return pool.getconn()

def execute(sql, *params):
    db = connect()
    c = db.cursor()
    args = [sql]
    if params:
        args.append(params)
    c.execute(*args)
    return list(c)

@functools.lru_cache()
def fetch_table(tbl):
    os.makedirs(os.path.expanduser("~/.cache/BioTK/table"), exist_ok=True)
    path = os.path.expanduser("~/.cache/BioTK/table/%s" % tbl)
    if os.path.exists(path):
        with open(path, "rb") as h:
            return pickle.load(h)
    q = "SELECT * FROM %s" % tbl
    db = connect()
    c = db.cursor()
    c.execute(q)
    columns = [d[0] for d in c.description]
    df = pd.DataFrame.from_records(c, columns=columns)
    with open(path, "wb") as h:
        pickle.dump(df, h)
    return df
