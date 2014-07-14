import psycopg2

from BioTK import CONFIG

def connect():
    return psycopg2.connect(
            database=CONFIG["db.name"], 
            user=CONFIG["db.user"],
            host=CONFIG["db.host"],
            port=int(CONFIG["db.port"]))


"""
from multicorn import ForeignDataWrapper

class BigWigFDW(ForeignDataWrapper):
    def __init__(self, options, columns):
        super(BigWigFDW, self).__init__(options, columns)
        self.columns = columns

    def execute(self, quals, columns):
        for index in range(20):
            line = {}
            for column_name in self.columns:
                line[column_name] = '%s %s' % (column_name, index)
            yield line
"""
