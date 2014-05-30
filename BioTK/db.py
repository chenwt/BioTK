import io
import glob
import gzip
import lzma
import os
import re
import sqlite3
import tarfile

import multiprocessing as mp

from sqlalchemy import create_engine, Column, Integer, String, \
        LargeBinary, Float, Boolean
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import sessionmaker, deferred
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import ARRAY

import pandas as pd
import numpy as np

import BioTK.io
import BioTK.util
from BioTK import LOG, CONFIG, TAXA

def read_dmp(handle, columns):
    """
    Read a NCBI .dmp file into a DataFrame.
    """
    buffer = io.StringIO()
    for i,line in enumerate(handle):
        buffer.write(line.rstrip("\t|\n") + "\n")
    buffer.seek(0)
    return pd.read_table(buffer, delimiter="\t\|\t", 
            names=columns,
            header=None)

########
# Models
########

Base = declarative_base()

class Taxon(Base):
    __tablename__ = "taxon"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    @staticmethod
    def objects(session):
        url = "ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz"
        cached_path = BioTK.io.download(url)
        with tarfile.open(cached_path, mode="r:gz") as archive:
            h = io.TextIOWrapper(archive.extractfile("names.dmp"),
                    encoding="utf-8")
            columns = ["id", "name", "_", "type"]
            data = read_dmp(h, columns)
            data = data.ix[data["id"].isin(TAXA),:]
            data = data.ix[data["type"] == "scientific name",["id","name"]]
            data = data.drop_duplicates("id").dropna()
            for id, name in data.to_records(index=False):
                yield Taxon(id=int(id), name=name)
    
class Gene(Base):
    __tablename__ = "gene"

    id = Column(Integer, primary_key=True)
    taxon_id = Column(Integer, ForeignKey("taxon.id"), nullable=False)
    symbol = Column(String)
    name = Column(String)

    @staticmethod
    def objects(session):
        #url = "ftp://ftp.ncbi.nih.gov/gene/DATA/gene_info.gz"
        #cached_path = BioTK.io.download(url)
        # FIXME: hardcoded path
        path = "/data/gene_info.gz"
        ids = set()
        nullable = lambda x: None if x == "-" else x
        with io.TextIOWrapper(gzip.open(path, "r"), encoding="utf-8") as h:
            next(h)
            for i,line in enumerate(h):
                if i and not i % 1000000:
                    LOG.debug("Processing gene_info.gz : line %s" % i)
                fields = line.split("\t")
                taxon_id = int(fields[0])
                if not taxon_id in TAXA:
                    continue
                id = int(fields[1])
                if id in ids:
                    continue
                ids.add(id)
                yield Gene(taxon_id=taxon_id, id=id,
                    symbol = nullable(fields[2]),
                    name = nullable(fields[11]))

class Genome(Base):
    __tablename__ = "genome"

    id = Column(Integer, primary_key=True)
    taxon_id = Column(Integer, ForeignKey("taxon.id"), nullable=False)
    key = Column(String, unique=True, nullable=False)
    provider = Column(String)

    def objects():
        rows = [(9606, "hg19", "UCSC")]
        for taxon_id, key, provider in rows:
            yield Genome(taxon_id=taxon_id, key=key, provider=provider)

class GEOPlatform(Base):
    __tablename__ = "geo_platform"

    id = Column(Integer, primary_key=True)
    taxon_id = Column(Integer, ForeignKey("taxon.id"), nullable=False)
    title = Column(String)

    @staticmethod
    def objects(session):
        # Is this name same as NCBI taxon name?
        taxon_name_to_id = {}
        for taxon in session.query(Taxon).all():
            if taxon.name:
                taxon_name_to_id[taxon.name] = taxon.id

        # FIXME: hardcoded path
        c = sqlite3.connect("/data/GEOmetadb.sqlite").cursor()
        c.execute("SELECT gpl, organism, title FROM gpl")
        for gpl, taxon_name, title in c:
            taxon_id = taxon_name_to_id.get(taxon_name)
            if taxon_id and (taxon_id in TAXA):
                yield GEOPlatform(
                        id=int(gpl.lstrip("GPL")),
                        taxon_id=taxon_id,
                        title=title)

class GEOSample(Base):
    """
    1-channel GEO samples
    """
    __tablename__ = "geo_sample"

    id = Column(Integer, primary_key=True)
    platform_id = Column(Integer, ForeignKey("geo_platform.id"))
    title = Column(String)
    description = Column(String)
    source = Column(String)
    characteristics = Column(String)
    data = deferred(Column(ARRAY(Float, dimensions=1, zero_indexes=True)))

    age = Column(Float)
    gender = Column(Integer)
    tissue = Column(String)
    cancer = Column(Boolean)

    @staticmethod
    def objects(session):
        # FIXME: cross-reference the organism to make sure there aren't
        # samples that are on a platform for one organism but used
        # data from another organism (e.g., some chimp samples on
        # human platforms)

        platforms = set([p.id for p in session.query(GEOPlatform).all()])
        c = sqlite3.connect("/data/GEOmetadb.sqlite").cursor()
        c.execute("""
        SELECT gsm, gpl, title, description, 
            source_name_ch1, characteristics_ch1
        FROM gsm
        WHERE channel_count = 1 AND type="RNA";
        """)
        for gsm, gpl, title, description, source, characteristics in c:
            platform_id = int(gpl.lstrip("GPL"))
            if not platform_id in platforms:
                continue
            yield GEOSample(platform_id=platform_id,
                id = int(gsm.lstrip("GSM")),
                title=title,
                description=description,
                source=source,
                characteristics=characteristics)

    @staticmethod
    def set_attributes():
        session = get_session()
        for sample in session.query(GEOSample):
            if sample.characteristics is None:
                continue
            m = re.search(r"\bage:\s*(?P<age>[0-9]+(\.[0-9])?)", 
                    sample.characteristics)
            if m is not None and m.group("age"):
                sample.age = float(m.group("age"))
            session.add(sample)
        session.commit()

######################
# Configure connection
######################

Session = sessionmaker()

# This connection is lazy; only initialized after
# the first SQLAlchemy query
#engine = create_engine("sqlite://")
def get_session(create=False):
    engine = create_engine(CONFIG["db.uri"])
    Session.configure(bind=engine)
    if create:
        Base.metadata.create_all(engine)
    return Session()

def fix_dtype(row):
    row = list(row)
    for i,e in enumerate(row):
        if e == np.nan:
            row[i] = None
        if isinstance(e, np.int32) or isinstance(e, np.int64):
            row[i] = int(e)
    return row

def populate_all(session):
    # The tables need to be populated in order b/c
    # some tables reference others
    classes = [Taxon, Gene, GEOPlatform, GEOSample]

    for cls in classes:
        if session.query(cls).count() > 0:
            continue
        if not hasattr(cls, "objects"):
            continue

        LOG.info("Loading data for DB table: '%s'" % cls.__tablename__)
        for objs in BioTK.util.chunks(cls.objects(session), 10000):
            session.add_all(objs)
            session.commit()
        LOG.info("Successfully loaded %d records into table: '%s'" % 
            (session.query(cls).count(), cls.__tablename__))

def load_expression_file(path):
    session = get_session()
    platform_id = int(os.path.basename(path).split(".")[0][3:])
    LOG.info("Inserting expression data for GEO platform: %d" \
            % platform_id)

    genes = np.array([g.id for g in \
            session.query(Gene)\
                .join(Taxon)\
                .join(GEOPlatform)\
                .filter(GEOPlatform.id==platform_id)\
                .order_by(Gene.id).all()])
    url = "ftp://ailun.stanford.edu/ailun/annotation/geo/GPL%s.annot.gz" \
            % platform_id
    annotation_path = BioTK.io.download(url)
    annotation = pd.read_table(annotation_path, 
            compression="gzip",
            usecols=[0,1],
            names=["Probe ID", "Gene ID"])
    probe_counts = annotation["Probe ID"].value_counts()
    unique_probes = probe_counts.index[probe_counts == 1]
    annotation.index = annotation["Probe ID"]
    annotation = annotation.ix[unique_probes, "Gene ID"]

    with tarfile.open(path, "r:xz") as archive:
        for chunk in BioTK.util.chunks(archive, 1000):
            for item in chunk:
                if not (item.name.startswith("GSM") and \
                        item.name.endswith("-tbl-1.txt")):
                    continue
                try:
                    sample_id = int(item.name.split("-")[0].lstrip("GSM"))
                    sample = session.query(GEOSample).get(sample_id)
                    if sample is None:
                        continue

                    handle = archive.extractfile(item)
                    # FIXME: read which column the value is in from the 
                    # included XML file (they aren't always in the same order)
                    expression = pd.read_table(handle, 
                            header=None, 
                            index_col=0,
                            names=["Probe ID", "Value"],
                            usecols=[0,1])
                    ix = annotation[expression.index].dropna()
                    mu = expression.groupby(ix).mean().iloc[:,0]
                    mu = mu + 1e-5 - mu.min()
                    if mu.max() > 100:
                        mu = mu.apply(np.log2)
                    mu = (mu - mu.mean()) / mu.std()
                    data = np.array(mu[genes])#.astype(np.float32).tostring()
                    sample.data = list(data) #lz4.dumps(data)
                    #LOG.debug("Inserted expression data for GEO sample: %d" 
                                #% sample_id)
                except:
                    pass
                    #LOG.debug("FAILED to insert expression data for GEO sample: %d" 
                            #% sample_id)
                #    pass
            session.commit()

def load_expression():
    miniml_dir = os.path.join(CONFIG["ncbi.geo.dir"], "miniml")
    paths = glob.glob(miniml_dir + "/GPL*.tar.xz")
    with mp.Pool(mp.cpu_count()) as pool:
        pool.map(load_expression_file, paths)

# FIXME: to properly load expression, need to increase max packet size:
# SET GLOBAL max_allowed_packet=1073741824;

if __name__ == "__main__":
    if CONFIG.getboolean("db.auto_populate"):
        #session = get_session(create=True)
        #populate_all(session)
        #load_expression()
        pass
    GEOSample.set_attributes()
