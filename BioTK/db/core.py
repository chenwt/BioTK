import io
import glob
import gzip
import lzma
import os
import re
import sqlite3
import tarfile

import multiprocessing as mp

import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String, \
        LargeBinary, Float, Boolean
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import sessionmaker, deferred
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.dialects.postgresql import HSTORE, ARRAY, DOUBLE_PRECISION
from sqlalchemy.orm import sessionmaker, deferred, relationship, backref
from sqlalchemy.ext.mutable import MutableDict

import pandas as pd
import numpy as np

import BioTK.io
import BioTK.util
from BioTK.data import GeneOntology
from BioTK import LOG, CONFIG

TAXA = set()

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

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

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
        taxa = set([t.id for t in session.query(Taxon)])
        with io.TextIOWrapper(gzip.open(path, "r"), encoding="utf-8") as h:
            next(h)
            for i,line in enumerate(h):
                if i and not i % 1000000:
                    LOG.debug("Processing gene_info.gz : line %s" % i)
                fields = line.split("\t")
                taxon_id = int(fields[0])
                if not taxon_id in taxa:
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

class Source(Base):
    __tablename__ = "source"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    @staticmethod
    def objects(session):
        yield Source(name="Gene Expression Omnibus")
        yield Source(name="Sequence Read Archive")

class Sample(Base):
    __tablename__ = "sample"

    id = Column(Integer, primary_key=True)
    taxon_id = Column(Integer, ForeignKey("taxon.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("source.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platform.id"), nullable=False)
    xref = Column(String)

    attributes = Column(MutableDict.as_mutable(HSTORE))

    age = Column(Float)
    gender = Column(Integer)

    _data = deferred(Column("data", ARRAY(DOUBLE_PRECISION, dimensions=1)))

    @staticmethod
    def objects(session):
        source = session.query(Source)\
                .filter_by(name="Gene Expression Omnibus").first()
        platforms = session.query(Platform)
        platforms = dict([(p.xref, p.id) for p in platforms])
        taxa = dict([(t.name, t.id) for t in session.query(Taxon)])
        db = sqlite3.connect("/data/public/ncbi/geo/GEOmetadb.sqlite")
        db.row_factory = dict_factory
        c = db.cursor()
        c.execute("""
        SELECT * FROM gsm
        WHERE channel_count = 1 AND type="RNA";
        """)
        for row in c:
            platform_id = platforms.get(row["gpl"])
            taxon_id = taxa.get(row["organism_ch1"])
            if (platform_id is None) or (taxon_id is None):
                continue
            s = Sample(
                    taxon_id=taxon_id,
                    source_id=source.id,
                    platform_id=platform_id,
                    attributes={},
                    xref=row["gsm"])
            for k, v in row.items():
                s.attributes[k] = str(v)
            yield s 

class Platform(Base):
    __tablename__ = "platform"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    xref = Column(String)

    @staticmethod
    def objects(session):
        # Is this name same as NCBI taxon name?
        taxon_name_to_id = {}
        for taxon in session.query(Taxon).all():
            if taxon.name:
                taxon_name_to_id[taxon.name] = taxon.id

        # FIXME: hardcoded path
        c = sqlite3.connect("/data/public/ncbi/geo/GEOmetadb.sqlite").cursor()
        c.execute("SELECT gpl, organism, title FROM gpl")
        for gpl, taxon_name, title in c:
            taxon_id = taxon_name_to_id.get(taxon_name)
            if taxon_id and (taxon_id in TAXA):
                yield Platform(
                        xref=gpl,
                        title=title)

# Ontology models

# TODO: 
# - maybe make a HasProbability mixin to inherit from?
# - have GEOSample inherit from a base Sample?

class Ontology(Base):
    __tablename__ = "ontology"

    id = Column(Integer, primary_key=True)
    abbreviation = Column(String)
    name = Column(String)
    terms = relationship("Term", backref="ontology")

    @staticmethod
    def objects(session):
        yield Ontology(abbreviation="GO", name="Gene Ontology")

class Term(Base):
    __tablename__ = "term"

    id = Column(Integer, primary_key=True)
    original_id = Column(Integer)
    ontology_id = Column(Integer, ForeignKey("ontology.id"))
    name = Column(String)
    synonyms = relationship("Synonym", backref="term")

    @property
    def accession(self):
        return "%s:%07d" % (self.ontology.abbreviation, self.original_id)

    @staticmethod
    def objects(session):
        ontology_id = session.query(Ontology)\
                .filter_by(abbreviation="GO")\
                .first().id
        go = GeneOntology()
        for id, name in zip(go.terms.index, go.terms["Name"]):
            if not id.startswith("GO:"):
                continue
            id = int(id.split(":")[1])
            yield Term(ontology_id=ontology_id,
                    original_id=id, name=name)

class Synonym(Base):
    __tablename__ = "synonym"

    id = Column(Integer, primary_key=True)
    term_id = Column(Integer, ForeignKey("term.id"))
    text = Column(String)

    @staticmethod
    def objects(session):
        ontology_id = session.query(Ontology)\
                .filter_by(abbreviation="GO")\
                .first().id
        go = GeneOntology()
        for id, synonym in zip(go.synonyms.index, go.synonyms["Synonym"]):
            if not id.startswith("GO:"):
                continue
            id = int(id.split(":")[1])
            term = session.query(Term)\
                    .join(Ontology)\
                    .filter(Ontology.abbreviation=="GO", 
                            Term.original_id==id)\
                    .first()
            if term is not None:
                yield Synonym(term_id=term.id, text=synonym)

class RelationType(Base):
    __tablename__ = "relation_type"

    id = Column(Integer, primary_key=True)
    name = Column(String)

class TermRelation(Base):
    __tablename__ = "term_term"
    __table_args__ = (
            sa.schema.CheckConstraint('term_term.log_probability <= 0'),
    )

    agent_id = Column(Integer, ForeignKey("term.id"), primary_key=True)
    target_id = Column(Integer, ForeignKey("term.id"), primary_key=True)
    type = Column(Integer, ForeignKey("relation_type.id"), primary_key=True)
    log_probability = Column(Float)

class GeneAnnotation(Base):
    __tablename__ = "term_gene"
    __table_args__ = (
            sa.schema.CheckConstraint('term_gene.log_probability <= 0'),
    )

    term_id = Column(Integer, ForeignKey("term.id"), primary_key=True)
    gene_id = Column(Integer, ForeignKey("gene.id"), primary_key=True)
    log_probability = Column(Float)

    @staticmethod
    def objects(session):
        pairs = set()
        go = GeneOntology()
        for taxon in session.query(Taxon):
            taxon_id = taxon.id
            annotation = go.annotation(taxon_id)
            for original_id, gene_id, _ in annotation.to_records(index=False):
                original_id = int(original_id.split(":")[1])
                gene_id = int(gene_id)
                term = session\
                        .query(Term)\
                        .filter(Ontology.abbreviation=="GO",
                                Term.original_id==original_id)\
                                        .first()
                if not (term.id, gene_id) in pairs:
                    pairs.add((term.id, gene_id))
                    yield GeneAnnotation(term_id=term.id, gene_id=gene_id,
                            log_probability=0)

class SampleAnnotation(Base):
    __tablename__ = "term_sample"
    __table_args__ = (
            sa.schema.CheckConstraint('term_sample.log_probability <= 0'),
    )

    term_id = Column(Integer, ForeignKey("term.id"), primary_key=True)
    sample_id = Column(Integer, ForeignKey("sample.id"), primary_key=True)
    log_probability = Column(Float)


# class SampleAnnotation

###################
# Text mining stuff
###################

"""
class Article(Base):
    id = Column(Integer, primary_key=True)
    title = Column(String)
    abstract = Column(String)
    full_text = Column(String)
"""

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
    classes = [Taxon, Gene, Source, Platform, Sample, 
        Ontology, Term, Synonym,
        GeneAnnotation]

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
