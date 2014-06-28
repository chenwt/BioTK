import os
import io
import tarfile
import gzip
import sqlite3
import glob
import datetime
import functools
from collections import namedtuple

import pandas as pd
import py2neo
from py2neo import neo4j
from celery import group, chord, chunks
from celery.signals import worker_process_init, task_prerun

from BioTK import CONFIG, LOG
import BioTK.io
from BioTK.io import MEDLINE, OBO

from . import *
from .util import *
from ..queue import QUEUE

batch = node_cache = None

@worker_process_init.connect
def initialize(sender, **kwargs):
    global batch, node_cache
    py2neo.packages.httpstream.http.ConnectionPool._puddles = {}
    reconnect()
    batch = BatchProxy()

    node_cache = {}
    _caches = [
        ("journal", "nlm_id"),
        ("taxon", "entrez_id"),
        ("taxon", "name"),
        ("platform", "gpl"),
        ("series", "gse"),
        ("publication", "pubmed_id"),
        ("ontology", "prefix"),
        ("term", "accession"),
        ("gene", "entrez_id"),
        ("sample", "gsm")
    ]

    for (label, key) in _caches:
        node_cache.setdefault(label, {})
        node_cache[label].setdefault(key, {})
        node_cache[label][key] = NodeCache(label, key)

#######
# Tasks
#######

def batch_insert(fn):
    @functools.wraps(fn)
    def decorator(records):
        for record in records:
            fn(*record)
        batch.run()
    return decorator

@QUEUE.task(ignore_result=True)
@batch_insert
def taxon_chunk(id, name):
    taxon_ix = node_index("taxon")
    n = batch.create_node(entrez_id=id, name=name)
    batch.add_labels(n, "taxon")
    batch.add_to_index(neo4j.Node, taxon_ix, 
            "entrez_id", id, n)
    batch.add_to_index(neo4j.Node, taxon_ix, 
            "name", name, n)
    batch.checkpoint()

def geo_connect():
    return sqlite3.connect("/data/public/ncbi/geo/GEOmetadb.sqlite")

def common_taxa():
    taxa = set()
    geo_db = geo_connect()
    c = geo_db.cursor()
    q = """
        select * from (
            select organism, count(organism) as c 
            from gpl 
            group by organism
        ) where c > 10;
        """
    for row in c.execute(q):
        if ";" not in row:
            taxa.add(row[0])
    geo_db.close()
    return taxa

@QUEUE.task
def taxon():
    taxa = common_taxa()
    taxon_ix = node_index("taxon")
    url = "ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz"
    cached_path = BioTK.io.download(url)
    with tarfile.open(cached_path, mode="r:gz") as archive:
        h = io.TextIOWrapper(archive.extractfile("names.dmp"),
                encoding="utf-8")
        columns = ["id", "name", "_", "type"]
        data = read_dmp(h, columns)
        data = data.ix[data["type"] == \
                "scientific name",["id","name"]]
        data = data.drop_duplicates("id").dropna()
        data = data[data["name"].isin(taxa)]

        records = ((int(id), str(name))
                for id, name in
                data.to_records(index=False))
        group((taxon_chunk.s(c) for c in BioTK.util.chunks(records)))()

@QUEUE.task
def gene_chunk(lines):
    gene_ix = node_index("gene")
    gene_ix_ft = node_index("gene", full_text=True)
    nullable = lambda x: None if x == "-" else x

    for line in lines:
        fields = line.split("\t")
        taxon = node_cache["taxon"]["entrez_id"].get(int(fields[0]))
        if taxon is None:
            continue
        gene_id = int(fields[1])
        attrs = {
                "entrez_id": gene_id, 
                "symbol": nullable(fields[2]),
                "name": nullable(fields[11]),
                "labels": ["gene"]
        }
        n = batch.create_node(**attrs)
        batch.add_to_index(neo4j.Node, gene_ix, "entrez_id", gene_id, n)
        if "symbol" in attrs:
            batch.add_to_index(neo4j.Node, gene_ix, 
                    "symbol", attrs["symbol"], n)
        if "name" in attrs:
            batch.add_to_index(neo4j.Node, gene_ix_ft,
                    "name", attrs["name"], n)
        batch.create_relation(n, "taxon", taxon)
        batch.checkpoint()
    batch.run()

@QUEUE.task
def gene():
    # batch is ignored here, and individual batches are created in
    # subprocesses
    url = "ftp://ftp.ncbi.nih.gov/gene/DATA/gene_info.gz"
    path = BioTK.io.download(url)
    ids = set()
    with io.TextIOWrapper(gzip.open(path, "r"), encoding="utf-8") as h:
        next(h)
        chunks = BioTK.util.chunks(h, 100000)
        group(gene_chunk.s(lines) for 
                lines in chunks)()

@QUEUE.task
def journal_file(path):
    journals = set()
    articles = MEDLINE.parse(path)
    for article in articles:
        journals.add(article.journal)
    return journals
  
@QUEUE.task
def journal_finish(results):
    journal_ix = node_index("journal")
    journals = set()
    for rs in results:
        journals = journals | rs
 
    for j in journals:
        if not (j.id and j.name):
            continue
        attrs = {"nlm_id": j.id, "issn": j.issn, 
                "name": j.name, "labels": ["journal"]}
        n = batch.create_node(**attrs)
        batch.add_to_index(neo4j.Node, journal_ix, "nlm_id", j.id, n)
        if "issn" in attrs:
            batch.add_to_index(neo4j.Node, journal_ix, "issn", j.issn, n)
        batch.checkpoint()
    batch.run()

@QUEUE.task
def journal():
    pattern = os.path.join(CONFIG["ncbi.medline.dir"], "*.xml.gz")
    paths = glob.glob(pattern)

    chord(journal_file.s(p) for p in paths)(
            journal_finish.s())()

@QUEUE.task
def publication_file(path):
    node_cache["journal"]["nlm_id"].fetch_all()
    publication_ix = node_index("publication")
    publication_ix_ft = node_index("publication", full_text=True)

    articles = list(MEDLINE.parse(path))

    for article in articles:
        if not article.id:
            continue
        attrs = {
                "pubmed_id": article.id,
        }
        index_title = index_abstract = False
        if article.title and isinstance(article.title, str):
            attrs["title"] = sanitize_string(article.title)
            index_title = True
        if article.publication_date:
            attrs["date"] = article.publication_date.toordinal()
        if article.abstract and isinstance(article.abstract, str):
            attrs["abstract"] = article.abstract
            index_abstract = True
        
        n = batch.create_node(labels=["publication"], **attrs)
        batch.add_to_index(neo4j.Node, publication_ix, "pubmed_id",
                article.id, n)
        if index_title:
            batch.add_to_index(neo4j.Node, publication_ix_ft, "title",
                    article.title, n)
        if index_abstract:
            batch.add_to_index(neo4j.Node, publication_ix_ft, "abstract",
                    article.abstract, n)

        journal = node_cache["journal"]["nlm_id"].get(article.journal.id)
        if journal is not None:
            batch.create_relation(n, "published_in", journal)
        batch.checkpoint()
    batch.run()

@QUEUE.task
def publication():
    pattern = os.path.join(CONFIG["ncbi.medline.dir"], "*.xml.gz")
    paths = sorted(glob.glob(pattern))
    group(publication_file.s(p) for p in paths)()

#####
# GEO
#####

@QUEUE.task
def platform():
    platform_ix = node_index("platform")

    geo_db = geo_connect()
    c = geo_db.cursor()

    c.execute("SELECT gpl, title, manufacturer FROM gpl")
    for gpl, title, manufacturer in c:
        n = batch.create_node(gpl=gpl, 
            title=title, 
            manufacturer=manufacturer,
            labels=["platform"])
        batch.add_to_index(neo4j.Node, platform_ix, "gpl", gpl, n)
        batch.checkpoint()
    batch.run()

@QUEUE.task
def series():
    series_ix = node_index("series")
    series_ix_ft = node_index("series", full_text=True)

    geo_db = geo_connect()
    c = geo_db.cursor()
    c.execute("SELECT * FROM gse")
    keys = [d[0] for d in c.description]
    for rows in BioTK.util.chunks(c):
        for row in rows:
            attrs = dict(zip(keys, row))
            try:
                date = datetime.date(*map(int, 
                    attrs["submission_date"].split("-")))\
                            .toordinal()
            except:
                date = None

            n = batch.create_node(
                gse=attrs["gse"],
                type=attrs["type"],
                summary=attrs["summary"],
                design=attrs["overall_design"],
                date=date,
                title=attrs["title"],
                labels=["series"])

            batch.add_to_index(neo4j.Node, series_ix, "gse", attrs["gse"], n)
            batch.add_to_index(neo4j.Node, series_ix_ft, 
                    "summary", attrs["summary"], n)
            batch.add_to_index(neo4j.Node, series_ix_ft, 
                    "title", attrs["title"], n)

            #publication = node_cache["publication"]["pubmed_id"]\
            #        .get(attrs.get("pubmed_id"))
            #if publication is not None:
            #    batch.create_relation(n, "publication", publication)
            batch.checkpoint()
        batch.run()

@QUEUE.task
def sample_chunk(keys, chunk):
    sample_ix = node_index("sample")
    node_cache["platform"]["gpl"].fetch_all()
    node_cache["taxon"]["name"].fetch_all()

    for row in chunk:
        attrs = dict(zip(keys, row))
        platform = node_cache["platform"]["gpl"].get(attrs["gpl"])
        taxon = node_cache["taxon"]["name"].get(attrs["organism_ch1"])
        if (platform is None) or (taxon is None):
            continue
        n = batch.create_node(
                labels=["sample"],
                gsm=attrs["gsm"],
                title=attrs["title"],
                type=attrs["type"],
                source=attrs["source_name_ch1"],
                molecule=attrs["molecule_ch1"],
                channel_count=attrs["channel_count"],
                description=attrs["description"],
                characteristics=attrs["characteristics_ch1"])
        batch.create_relation(n, "taxon", taxon)
        batch.create_relation(n, "part_of", platform)
        batch.add_to_index(neo4j.Node, sample_ix, "gsm", attrs["gsm"], n)
        if attrs["series_id"]:
            gsms = attrs["series_id"].split(",")
            for gsm in gsms:
                series = node_cache["series"]["gse"].get(gsm)
                if series is not None:
                    batch.create_relation(n, "part_of", series)
        batch.checkpoint()
    batch.run()

@QUEUE.task
def sample():
    geo_db = geo_connect()
    c = geo_db.cursor()
    c.execute("""SELECT * FROM gsm""")
    keys = [d[0] for d in c.description]
    chunks = BioTK.util.chunks(c)
    group(sample_chunk.s(keys, chunk) for chunk in chunks)()

############
# Ontologies
############

OBO_DIR = "/data/public/ontology/obo"

ontologies = {
        "BTO": "Brenda Tissue Ontology",
        "PATO": "Phenotypic Quality Ontology",
        "GO": "Gene Ontology",
}

def read_obo(ontology_prefix):
    path = os.path.join(OBO_DIR, ontology_prefix+".obo")
    if not os.path.exists(path):
        raise IOError("Expected OBO file does not exist at path: %s" \
                % path)
    with open(path) as h:
        return OBO.parse(h)

@QUEUE.task
def ontology():
    ontology_ix = node_index("ontology")

    for prefix, name in ontologies.items():
        o = batch.create_node(prefix=prefix, name=name, 
                labels=["ontology"])
        batch.add_to_index(neo4j.Node, ontology_ix, "prefix", 
                prefix, o)
        batch.add_to_index(neo4j.Node, ontology_ix, "name", 
                name, o)
    batch.run()

Ontology = namedtuple("Ontology", "node,data")

def get_ontologies():
    node_cache["ontology"]["prefix"].fetch_all()
    for prefix, ontology in node_cache["ontology"]["prefix"].items():
        data = read_obo(prefix)
        yield Ontology(ontology, data)

@QUEUE.task
def term_chunk(ontology_prefix, records):
    term_ix = node_index("term")
    term_ft_ix = node_index("term", full_text=True)
    ontology = node_cache["ontology"]["prefix"].get(ontology_prefix)

    for accession, name, namespace in records:
        prefix, term_id = accession.split(":")
        term_id = int(term_id)
        t = batch.create_node(id=term_id, name=name, 
                namespace=namespace,
                accession=accession,
                labels=["term"])
        batch.add_to_index(neo4j.Node, term_ix, "id", term_id, t)
        batch.add_to_index(neo4j.Node, term_ix, "namespace", 
                namespace, t)
        batch.add_to_index(neo4j.Node, term_ix, "accession", 
                accession, t)
        batch.add_to_index(neo4j.Node, term_ft_ix, "name", name, t)
        batch.create_relation(t, "part_of", ontology)
        batch.checkpoint()
    batch.run()

@QUEUE.task
def term():
    for o in get_ontologies():
        records = (list(map(str, row)) for row in 
            o.data.terms.to_records(index=True))
        group(term_chunk.s(o.node["prefix"], chunk) for chunk
                in BioTK.util.chunks(records))()

@QUEUE.task
def term_term_chunk(records):
    node_cache["term"]["accession"].fetch_all()
    for n1, n2, r_type in records:
        n1 = node_cache["term"]["accession"].get(n1)
        n2 = node_cache["term"]["accession"].get(n2)
        r = batch.create_relation(n1, r_type, n2)
        batch.checkpoint()
    batch.run()

@QUEUE.task
def term_term():
    for o in get_ontologies():
        records = (list(map(str, r)) for r in 
                o.data.relations.to_records(index=False))
        group(term_term_chunk.s(chunk) for chunk
                in BioTK.util.chunks(records, 10000))()

@QUEUE.task
def term_synonym_chunk(records):
    node_cache["term"]["accession"].fetch_all()
    synonym_ix = node_index("synonym", full_text=True)
    for term_accession, synonym in records:
        t = node_cache["term"]["accession"].get(term_accession)
        if t:
            s = batch.create_node(text=synonym, labels=["synonym"])
            batch.add_to_index(neo4j.Node, synonym_ix, "text", "text", s)
            batch.create_relation(s, "synonym_of", t)
        batch.checkpoint()
    batch.run()

@QUEUE.task
def term_synonym():
    for o in get_ontologies():
        records = (list(map(str, r)) for r in 
                o.data.synonyms.to_records(index=True))
        group(term_synonym_chunk.s(chunk) for chunk
                in BioTK.util.chunks(records))()

##########
# Mappings
##########

@QUEUE.task
def gene_go_chunk(chunk):
    node_cache["term"]["accession"].fetch_all()
    node_cache["gene"]["entrez_id"].fetch_all()
    for gene_id, term_accession, evidence in chunk:
        gene = node_cache["gene"]["entrez_id"].get(gene_id)
        term = node_cache["term"]["accession"].get(term_accession)
        if (gene is not None) and (term is not None):
            r = batch.create_relation(gene, "annotated_with", term, 
                    source="GO Consortium",
                    evidence=evidence)
        batch.checkpoint()
    batch.run()

@QUEUE.task
def gene_go():
    url = "ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2go.gz"
    path = BioTK.io.download(url)
    with gzip.open(path, "r") as h:
        df = pd.read_table(h, skiprows=1, 
                header=None, names=("Taxon ID", "Gene ID", "Term ID", 
                    "Evidence", "Qualifier", "TermName", "PubMed", "Category"))
        records = df.iloc[:,1:4].itertuples(index=False)
        group(gene_go_chunk.s(chunk)
                for chunk in BioTK.util.chunks(records))()

@QUEUE.task
def sample_term_bto_ursa(db, batch):
    url = "http://ursa.princeton.edu/supp/manual_annotations_ursa.csv"
    path = BioTK.io.download(url)
    evidence = "manual"
    source = "URSA"
    q = """MATCH (t:`term`)-[:part_of]-(o) 
           WHERE o.prefix='BTO' 
           RETURN t.name,t"""
    bto_by_name = dict(get_cypher().execute(q))

    with open(path) as h:
        next(h)
        for line in h:
            gsm, _, bto_name = line.split("\t")
            term = bto_by_name.get(bto_name)
            sample = node_index["sample"]["gsm"].get(gsm)
            if (term is not None) and (sample is not None):
                r = batch.create_relation(sample, "annotated_with", term, 
                        source=source,
                        evidence=evidence)
