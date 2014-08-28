import psycopg2

from BioTK import CONFIG

DECIMAL_TO_FLOAT = psycopg2.extensions.new_type(
        psycopg2.extensions.DECIMAL.values,
        'DECIMAL_TO_FLOAT',
        lambda value, curs: float(value) if value is not None else None)
psycopg2.extensions.register_type(DECIMAL_TO_FLOAT)

def connect():
    return psycopg2.connect(
            database=CONFIG["db.name"], 
            user=CONFIG["db.user"],
            host=CONFIG["db.host"],
            port=int(CONFIG["db.port"]))
