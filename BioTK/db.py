import psycopg2

from BioTK import CONFIG

def connect():
    return psycopg2.connect(
            database=CONFIG["db.name"], 
            user=CONFIG["db.user"],
            host=CONFIG["db.host"],
            port=int(CONFIG["db.port"]))
