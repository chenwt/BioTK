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
from sqlalchemy.orm import sessionmaker, deferred, relationship, backref

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

    genes = relationship("Gene", backref="taxon")

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
        url = "ftp://ftp.ncbi.nih.gov/gene/DATA/gene_info.gz"
        path = BioTK.io.download(url)
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

# Ontology models

class Ontology(Base):
    __tablename__ = "ontology"

    id = Column(Integer, primary_key=True)
    abbreviation = Column(String)
    name = Column(String)
    terms = relationship("Term", backref="ontology")

class Term(Base):
    __tablename__ = "term"

    id = Column(Integer, primary_key=True)
    original_id = Column(Integer)
    ontology_id = Column(Integer, ForeignKey("ontology.id"))
    name = Column(String)
    synonyms = relationship("Synonym", backref="term")

class RelationType(Base):
    __tablename__ = "relation_type"

    id = Column(Integer, primary_key=True)
    name = Column(String)

class TermRelation(Base):
    __tablename__ = "term_relation"

    agent_id = Column(Integer, ForeignKey("term.id"), primary_key=True)
    target_id = Column(Integer, ForeignKey("term.id"), primary_key=True)
    type = Column(Integer, ForeignKey("relation.id"), primary_key=True)
    probability = Column(Float)

class Synonym(Base):
    __tablename__ = "synonym"

    id = Column(Integer, primary_key=True)
    term_id = Column(Integer, ForeignKey("term.id"))
    text = Column(String)

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

if __name__ == "__main__":
    if CONFIG.getboolean("db.auto_populate"):
        session = get_session(create=True)
        populate_all(session)
    GEOSample.set_attributes()
