import sqlite3
from collections import namedtuple, defaultdict

import BioTK.io

Sample = namedtuple("Sample",
        ["accession", "channel", "experiments",
            "organism", "platform",
            "title", "description", "characteristics", "source"])
Sample.text = property(lambda s: "\n".join(map(lambda x: x or "", 
    [s.title, s.description, s.characteristics, s.source])))

Experiment = namedtuple("Experiment",
        ["accession", "title", "summary", "design"])
Experiment.text = property(lambda s: "\n".join(map(lambda x: x or "", 
    [s.title, s.summary, s.design])))

class GEOMetaDB(object):
    def __init__(self, path=None):
        if path is None:
            url = "http://gbnci.abcc.ncifcrf.gov/geo/GEOmetadb.sqlite.gz"
            path = BioTK.io.download(url, unzip="gzip", open=False)
        self._db = sqlite3.connect(path)

    def __del__(self):
        self._db.close()

    @property
    def samples(self):
        c = self._db.cursor()
        m = defaultdict(set)
        c.execute("""SELECT gsm,gse FROM gse_gsm""")
        for gsm,gse in c:
            m[gsm].add(gse)    

        for i in [1,2]:
            c.execute("""
                SELECT gsm,gpl,
                    title,description,characteristics_ch%s,organism_ch%s,source_name_ch%s
                FROM gsm
                WHERE 
                organism_ch1='Homo sapiens'
                AND
                molecule_ch1='total RNA'
                AND
                channel_count >= %s""" % (i,i,i,i))
            for gsm,gpl,title,desc,ch,species,source in c:
                yield Sample(gsm,i,m[gsm],species,gpl,title,desc,ch,source)

    @property
    def experiments(self):
        c = self._db.cursor()
        c.execute("""
            SELECT gse,title,summary,overall_design
            FROM gse""")
        for row in c:
            yield Experiment(*row)
