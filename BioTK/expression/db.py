import gzip
import os
import tarfile
from xml.etree import ElementTree
import sqlite3
import collections
import sys

import pandas as pd
import numpy as np

import BioTK

# TODO: split out MiniML parsing from DB?

NS = "{http://www.ncbi.nlm.nih.gov/geo/info/MINiML}"

def clean(s):
    return s.replace("\n", " ").replace("\t", " ").strip()

class Platform(object):
    def __init__(self, db, platform_id):
        self._db = db
        self._id = id

    def feature_attributes(self):
        c = self._db.cursor()
        c.execute("""SELECT name FROM feature_metadata
            WHERE platform_id=?
            ORDER BY column_index""", (self._id,))
        columns = [r[0] for r in c]

        c.execute("""
            SELECT row_index, column_index, value
            FROM feature
            WHERE platform_id=?""", (platform_id,))
        df = pd.DataFrame.from_records(c, columns=["Row","Column","Value"])\
                .pivot(index="Row", columns="Column", values="Value")
        df.columns = columns
        return df.set_index(df.columns[0])

    def sample_attributes(self):
        c = self._db.cursor()
        c.execute("""SELECT "GSM" || CAST(id AS text),
                title,description,channel_count 
            FROM sample
            WHERE id IN (%s)""" % ",".join(list(map(str,samples))))
        return pd.DataFrame.from_records(c,
                columns=["Sample ID","Title","Description","Channel Count"])\
                        .set_index("Sample ID")

    def sample_characteristics(self):
        c = self._db.cursor()
        pass

    def expression(self):
        platform_id = list(self._samples.keys())[0]
        samples = list(self._samples.values())[0]
        c = self._db.cursor()
        c.execute("""SELECT value FROM feature
            WHERE column_index=0
            AND platform_id=?
            ORDER BY row_index""", (platform_id,))
        row_index = [r[0] for r in c]
        c.execute("""SELECT sample_id, data FROM sample_data 
            WHERE sample_id IN (%s)
            AND channel=1""" % ",".join(list(map(str, samples))))
        columns = dict([("GSM"+str(id),np.fromstring(data)) 
            for (id, data) in c])
        X = pd.DataFrame.from_dict(columns)
        X.index = row_index
        return X

class ExpressionDB(object):
    LOCK_TIMEOUT = 300

    def __init__(self, path):
        create = not os.path.exists(path)
        #uri = "file:%s?mode=ro" % path
        uri = "file:%s" % path
        self._db = sqlite3.connect(uri, self.LOCK_TIMEOUT, uri=True)
        if create:
            schema_path = BioTK.data_path("schema.sql")
            with open(schema_path) as h:
                c = self._db.cursor()
                c.executescript(h.read())

    def __del__(self):
        self.close()

    def close(self):
        self._db.close()

    def __getitem__(self, query):
        assert query.startswith("GPL")
        platform_id = int(query[3:])
        return Platform(self._db, platform_id)

    def _load_miniml_xml(self, h):
        c = self._db.cursor()
        tree = ElementTree.iterparse(h)

        for _, e in tree:
            if e.tag == NS+"Platform":
                gpl = e.attrib["iid"]
                platform_id = int(gpl[3:])
                title = e.find(NS+"Title").text
                manufacturer = e.find(NS+"Manufacturer").text
                taxon_id = int(e.find(NS+"Organism").attrib["taxid"])

                c.execute("""INSERT OR REPLACE INTO platform 
                    (id, title, manufacturer, taxon_id)
                    VALUES
                    (?, ?, ?, ?)""", 
                    (platform_id, title, manufacturer, taxon_id))

                tbl = e.find(NS+"Data-Table")
                records = []
                for col in tbl.findall(NS+"Column"):
                    index = int(col.attrib["position"]) - 1
                    name = clean(col.find(NS+"Name").text)
                    desc_node = col.find(NS+"Description")
                    description = clean(desc_node.text if desc_node else "")
                    c.execute("""INSERT OR REPLACE INTO feature_metadata
                        (platform_id, column_index, name, description)
                        VALUES (?,?,?,?)""", 
                        (platform_id, index, name, description))

            elif e.tag == NS+"Sample":
                try:
                    sample_id = int(e.attrib["iid"][3:])
                    title_node = e.find(NS+"Title")
                    title = clean(title_node.text.strip() 
                            if title_node else "")
                    desc_node = col.find(NS+"Description")
                    description = clean(desc_node.text.strip() 
                            if desc_node else "")
                    try:
                        platform_id = \
                                int(e.find(NS+"Platform-Ref")\
                                .attrib["ref"][3:])
                    except AttributeError:
                        # This must be a platform-based MiniML, so fall back
                        # to the platform ID from above
                        pass
                    channel_count = int(e.find(NS+"Channel-Count").text)
                    c.execute("""INSERT OR REPLACE INTO sample
                        (id, platform_id, title, description, channel_count)
                        VALUES (?,?,?,?,?)""",
                        (sample_id, platform_id, title, 
                            description, channel_count))

                    for channel_node in e.findall(NS+"Channel"):
                        channel = int(channel_node.attrib["position"])
                        for ch in channel_node.findall(NS+"Characteristics"):
                            if not "tag" in ch.attrib:
                                continue
                            c.execute("""INSERT OR REPLACE 
                                INTO sample_characteristic
                                (sample_id, channel, key, value)
                                VALUES (?,?,?,?)""",
                                (sample_id, channel, clean(ch.attrib["tag"]), 
                                    clean(ch.text)))
                except AttributeError:
                    pass

            elif e.tag == NS+"Series":
                series_id = int(e.attrib["iid"][3:])
                title = e.find(NS+"Title").text.strip()
                summary = e.find(NS+"Summary").text.strip()
                overall_design = e.find(NS+"Overall-Design").text.strip()
                c.execute("""INSERT OR REPLACE INTO series
                    (id, title, summary, overall_design)
                    VALUES (?,?,?,?)""", 
                    (series_id, title, summary, overall_design))

                for sr in e.findall(NS+"Sample-Ref"):
                    sample_id = int(sr.attrib["ref"][3:])
                    c.execute("""INSERT OR REPLACE INTO series_sample
                        (series_id, sample_id)
                        VALUES (?,?)""", (series_id, sample_id))

        self._db.commit()

    def load(self, path):
        """
        Load the contents of a MiniML-format .tar.gz file 
        from GEO into the database.
        """
        c = self._db.cursor()
        probes = {}
        with tarfile.open(path, "r:xz", encoding="utf-8") as tgz:
            for ti in tgz:
                with tgz.extractfile(ti) as h:
                    print(ti.name)
                    if ti.name.endswith(".xml") and ti.isreg():
                        # For broken XML in GPL570...
                        import io, re
                        h = io.StringIO(re.sub("\x19", "", 
                            h.read().decode("utf-8")))
                        self._load_miniml_xml(h)
                    elif ti.name.startswith("GPL"):
                        # FIXME: don't re-insert if already exists, 
                        # but always pull down array of probe indexes
                        platform_id = int(ti.name.split("-")[0][3:])
                        df = pd.read_table(h, header=False)
                        N, K = df.shape
                        rows = zip(
                                map(int, np.repeat(platform_id, N*K)),
                                map(int, np.tile(np.arange(N), K)),
                                map(int, np.arange(K).repeat(N)),
                                df.values.ravel("F"))
                        c.executemany("""INSERT INTO feature
                            (platform_id, row_index, column_index, value)
                            VALUES (?,?,?,?)""", rows)

                        c.execute("""SELECT value FROM feature
                            WHERE platform_id=? AND column_index=0
                            ORDER by row_index""", (platform_id,))
                        probes[platform_id] = np.array([r[0] for r in c])

        with tarfile.open(path, "r:xz", encoding="utf-8") as tgz:
            for ti in tgz:
                if ti.name.startswith("GSM") and ti.name.endswith(".txt"):
                    with tgz.extractfile(ti) as h:
                        sample_id = int(ti.name.split("-")[0][3:])
                        print("Inserting GSM:", sample_id, file=sys.stderr)

                        channel = int(ti.name.split("-")[2].rstrip(".txt"))
                        c.execute("""SELECT platform_id FROM sample 
                            WHERE id=? LIMIT 1""", (sample_id,))
                        platform_id = next(c)[0]
                        data = pd.read_table(h, index_col=0, header=False)\
                                .iloc[:,0]\
                                .ix[probes[platform_id]]
                        data = np.array(data)
                        data = data.tostring()
                        c.execute("""INSERT INTO sample_data
                            (sample_id, channel, data)
                            VALUES (?,?,?)""", (sample_id, channel, data))
        self._db.commit()

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--database_path", "-d", required=True)
    p.add_argument("archives", nargs="+")
    args = p.parse_args()

    db = ExpressionDB(args.database_path)
    for archive in args.archives:
        db.load(archive)
