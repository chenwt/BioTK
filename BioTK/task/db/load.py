#!/usr/bin/env python

import io
import gzip
import re
import os
import functools
import tempfile
import subprocess as sp

import click
import sqlite3
import sys
import tarfile

import numpy as np
import pandas as pd
import psycopg2
from celery import group

from BioTK import LOG, CONFIG
from BioTK.cache import cached, download
from BioTK.io import OBO
from BioTK.db import connect

from ..queue import QUEUE

def bulk_load(path, table, *columns):
    with open(path) as h:
        LOG.info("Bulk loading %s from %s" % (table, path))
        sp.call(["sort", "-S", "4G", "-u", "-o", path, path])
        sp.check_output(["psql", 
            "-d", CONFIG["db.name"], 
            "-h", CONFIG["db.host"],
            CONFIG["db.user"], 
            "-c", "COPY %s (%s) FROM STDIN NULL 'None'" % \
                (table, ", ".join(columns))],
            stdin=h)

# FIXME add FIFO and concurrently load with psql
def bulk_load_generator(generator, table, *columns):
    with tempfile.NamedTemporaryFile("wt") as h:
        for row in generator:
            row = list(map(lambda x: 
                str(x)\
                        .replace("\\\\", "")\
                        .replace("\\", "")\
                        .replace("\t", " ")\
                        .replace("\n", " ")\
                        .replace("\r", " "), row))
            h.write("\t".join(row)+"\n")
        h.flush()
        bulk_load(h.name, table, *columns)

def ensure_inserted_and_get_index(table, key, items):
    for item in items:
        if item is not None:
            cursor.execute("SELECT * FROM {table} WHERE {key}=%s;"\
                    .format(table=table,key=key), (item,))
            try:
                next(cursor)
            except StopIteration:
                cursor.execute("INSERT INTO {table} ({key}) VALUES (%s);"\
                        .format(table=table,key=key), (item,))
    connection.commit()
    cursor.execute("SELECT {key},id FROM {table};".format(**locals()))
    return dict(cursor)

def is_empty(table):
    cursor.execute("SELECT * FROM {table} LIMIT 1".format(table=table))
    try:
        next(cursor)
        return False
    except StopIteration:
        return True

def mapq(q):
    cursor.execute(q)
    return dict(cursor)

def populates(*tables, check_query=None):
    # check_query is a SQL query which returns >1 rows if
    # the function does not need to be run, or 0 rows if
    # the function needs to be run.
    def decorator(fn): 
        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            if check_query is not None:
                cursor.execute(check_query)
                try:
                    next(cursor)
                    needed = False
                except StopIteration:
                    needed = True
            elif tables:
                needed = all(is_empty(tbl) for tbl in tables)
            else:
                assert False

            if needed:
                LOG.info("Executing %s" % fn.__name__)
                rs = fn(*args, **kwargs)
                connection.commit()
            else:
                LOG.info("Skipping %s" % fn.__name__)
        return wrap
    return decorator

def read_dmp(handle, columns):
    """
    Read a NCBI .dmp file into a DataFrame.
    """
    buffer = io.StringIO()
    for i,line in enumerate(handle):
        buffer.write(line.rstrip("\t|\n") + "\n")
    buffer.seek(0)
    return pd.read_table(buffer, delimiter="\t\|\t", 
            engine="python",
            names=columns,
            header=None)

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

########
# Schema
########

def ensure_schema():
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema='public';
        """)
    count = next(cursor)[0]
    if count == 0:
        LOG.info("Loading schema")
        with open("resources/sql/schema.sql") as h:
            cursor.execute(h.read())
            connection.commit()

#########
# Loaders
#########

@populates("taxon")
def load_taxon():
    taxa = common_taxa()
    url = "ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz"
    cached_path = download(url)
    with tarfile.open(cached_path, mode="r:gz") as archive:
        h = io.TextIOWrapper(archive.extractfile("names.dmp"),
                encoding="utf-8")
        columns = ["id", "name", "_", "type"]
        data = read_dmp(h, columns)
        data = data.ix[data["type"] == \
                "scientific name",["id","name"]]
        data = data.drop_duplicates("id").dropna()
        data = data[data["name"].isin(taxa)]
        cursor.executemany("""
            INSERT INTO taxon (id, name) VALUES (%s,%s);
            """, ((int(id), str(name))
                for id, name in
                data.to_records(index=False)))

@populates("gene")
def load_gene():
    cursor.execute("SELECT id FROM taxon;")
    taxa = set([r[0] for r in cursor])

    url = "ftp://ftp.ncbi.nih.gov/gene/DATA/gene_info.gz"
    path = download(url)
    with tempfile.NamedTemporaryFile("wt") as o:
        nullable = lambda x: None if x == "-" else x
        with io.TextIOWrapper(gzip.open(path, "r"), encoding="utf-8") as h:
            next(h)
            for line in h:
                fields = line.split("\t")
                taxon_id = int(fields[0])
                if taxon_id not in taxa:
                    continue
                gene_id = int(fields[1])
                symbol = nullable(fields[2])
                name = nullable(fields[11])
                row = list(map(str, (taxon_id, gene_id, symbol, name)))
                o.write("\t".join(row) + "\n")
        o.flush()
        bulk_load(o.name, "gene", "taxon_id", "id", "symbol", "name")

def load_ontology(prefix, name, path):
    cursor.execute("""
        INSERT INTO ontology (prefix,name) VALUES (%s,%s) RETURNING id""",
            (prefix, name))
    ontology_id = next(cursor)[0]

    with open(path) as h:
        o = OBO.parse(h)

    # Insert (if necessary) and cache namespaces
    namespace_to_id = ensure_inserted_and_get_index( 
            "namespace", "text", o.terms["Namespace"])
    accession_to_id = {}

    # Insert terms
    for accession, name, namespace in o.terms.to_records(index=True):
        if isinstance(namespace, list) or namespace is None:
            # FIXME
            namespace_id = None
        else:
            namespace_id = namespace_to_id[namespace]
        cursor.execute("""
        INSERT INTO term (ontology_id,namespace_id,accession,name)
        VALUES (%s,%s,%s,%s)
        RETURNING id;
        """, (ontology_id,namespace_id,accession,name))
        accession_to_id[accession] = next(cursor)[0]
                    
    # Insert synonyms
    synonyms = o.synonyms
    synonym_to_id = ensure_inserted_and_get_index(
            "synonym", "text", set(synonyms["Synonym"]))

    # Insert term-synonym links
    for accession, synonym in synonyms.to_records():
        term_id = accession_to_id[accession]
        synonym_id = synonym_to_id[synonym]
        cursor.execute("INSERT INTO term_synonym VALUES (%s,%s)",
                (term_id,synonym_id))
       
    # Insert relationships    
    relationship_to_id = ensure_inserted_and_get_index(
            "relationship", "name", set(o.relations["Relation"]))

    # Insert term-term links
    inserted_terms = set(o.terms.index)
    for agent, target, r in o.relations.to_records(index=False):
        agent_id = accession_to_id.get(agent)
        target_id = accession_to_id.get(target)
        if (agent_id is None) or (target_id is None):
            continue
        relationship_id = relationship_to_id[r]
        cursor.execute("""
        INSERT INTO term_term (agent_id,target_id,relationship_id)
        VALUES (%s,%s,%s);
        """, (agent_id, target_id, relationship_id))

OBO_PATH = "/data/public/ontology/obo/"
ONTOLOGIES = [
        ("GO", "Gene Ontology"),
        ("BTO", "Brenda Tissue Ontology"),
        ("PATO", "Phenotypic Quality Ontology")
]

@populates("ontology", "term")
def load_ontologies():
    for prefix, name in ONTOLOGIES:
        LOG.debug("Loading data for %s (%s)" % (prefix, name))
        load_ontology(prefix, name, OBO_PATH+prefix+".obo")

@populates("platform")
def load_platform():
    geo_db = geo_connect()
    gc = geo_db.cursor()

    source = "Gene Expression Omnibus"
    source_id = ensure_inserted_and_get_index("source", "name", 
            [source])[source]

    gc.execute("SELECT %s,gpl,title,manufacturer FROM gpl;" % source_id)
    for r in gc:
        cursor.execute("""
            INSERT INTO platform (source_id,accession,title,manufacturer) 
            VALUES (%s,%s,%s,%s)
            RETURNING id;""", r)

@populates("series")
def load_series():
    geo_db = geo_connect()
    gc = geo_db.cursor()
    source = "Gene Expression Omnibus"
    source_id = ensure_inserted_and_get_index("source", "name", 
            [source])[source]
    gc.execute("""
        SELECT gse,%s,type,summary,overall_design,submission_date,title 
        FROM gse;""" % source_id)
    bulk_load_generator(gc, "series", "accession", "source_id",
        "type", "summary", "design", "submission_date", "title")

@populates("sample")
def load_sample():
    gpl_to_id = mapq("SELECT accession,id FROM platform;")

    geo_db = geo_connect()
    gc = geo_db.cursor()
    gc.execute("""
        SELECT gpl,gsm,title,status,submission_date,last_update_date,
            type,hyb_protocol,description,data_processing,
            contact,supplementary_file,channel_count
        FROM gsm;""")
    def generate():
        for row in gc:
            row = list(row)
            row[0] = gpl_to_id.get(row[0])
            if not row[0]:
                continue
            row[-1] = int(row[-1])
            yield row
    bulk_load_generator(generate(), "sample", 
            "platform_id", "accession", "title", "status", 
            "submission_date", "last_update_date", 
            "type", "hybridization_protocol", "description",
            "data_processing", "contact", "supplementary_file",
            "channel_count")

@populates("sample_series")
def load_sample_series():
    geo_db = geo_connect()
    gc = geo_db.cursor()
    gsm_to_id = mapq("SELECT accession,id FROM sample;")
    gse_to_id = mapq("SELECT accession,id FROM series;")
    gc.execute("""
        SELECT gse_gsm.gsm,gse
        FROM gse_gsm
        INNER JOIN gsm
        ON gsm.gsm=gse_gsm.gsm;""")
    def generate():
        for gsm,gse in gc:
            sample_id = gsm_to_id.get(gsm)
            series_id = gse_to_id.get(gse)
            if sample_id and series_id:
                yield (gsm_to_id[gsm],gse_to_id[gse])
    bulk_load_generator(generate(), "sample_series",
            "sample_id", "series_id")

@populates("channel")
def load_channel():
    taxon_to_id = mapq("SELECT name,id FROM taxon;")
    gsm_to_id = mapq("SELECT accession,id FROM sample;")
    geo_db = geo_connect()
    gc = geo_db.cursor()
    
    def generate():
        for ch in [1,2]:
            q = """
                SELECT gsm,{n},organism_ch{n},source_name_ch{n},
                    characteristics_ch{n},molecule_ch{n},
                    label_ch{n}, treatment_protocol_ch{n},
                    extract_protocol_ch{n},label_protocol_ch{n}
                FROM gsm
                WHERE channel_count >= {n};""".format(n=ch)
            gc.execute(q)
            for row in gc:
                row = list(row)
                row[0] = gsm_to_id.get(row[0])
                row[2] = taxon_to_id.get(row[2])
                if row[0] is None or row[2] is None:
                    continue
                yield row
    bulk_load_generator(generate(), "channel",
            "sample_id", "channel", "taxon_id",
            "source_name", "characteristics", "molecule",
            "label", "treatment_protocol",
            "extract_protocol", "label_protocol")
        
############################################
# Manual or official gene/sample annotations
############################################

check_gene_go = """
    SELECT * FROM term_gene
    INNER JOIN source
    ON source.id=term_gene.source_id
    WHERE source.name='Gene Ontology Consortium'
    LIMIT 1;"""

@populates(check_query=check_gene_go)
def load_gene_go():
    accession_to_term_id = mapq("select accession,id FROM term")
    source = "Gene Ontology Consortium"
    source_id = ensure_inserted_and_get_index("source","name",
            [source])[source]
    cursor.execute("SELECT id FROM gene;")
    genes = set(row[0] for row in cursor)

    url = "ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2go.gz"
    path = download(url)
    with gzip.open(path, "r") as h:
        df = pd.read_table(h, skiprows=1, 
                header=None, names=("Taxon ID", "Gene ID", "Term ID", 
                    "Evidence", "Qualifier", "TermName", "PubMed", "Category"))
        df = df[df["Gene ID"].isin(genes)]
        evidence_to_id = ensure_inserted_and_get_index("evidence","name",
                set(df["Evidence"]))
        records = ((accession_to_term_id[term_accession], int(gene_id),
                evidence_to_id[evidence], source_id)
                for gene_id,term_accession,evidence 
                in df.iloc[:,1:4].dropna().itertuples(index=False))
        bulk_load_generator(records, "term_gene",
                "term_id","gene_id","evidence_id","source_id")

check_ursa = """
    SELECT * FROM term_channel
    INNER JOIN source
    ON term_channel.source_id=source.id
    WHERE source.name='URSA'
    LIMIT 1;
    """

@populates(check_query=check_ursa)
def load_ursa():
    url = "http://ursa.princeton.edu/supp/manual_annotations_ursa.csv"
    path = download(url)
    evidence = "manual"
    evidence_id = ensure_inserted_and_get_index(
            "evidence","name",[evidence])[evidence]
    source = "URSA"
    source_id = ensure_inserted_and_get_index(
            "source", "name", [source])[source]

    sample_accession_to_id = mapq("SELECT accession,id FROM sample;")
    term_name_to_id = mapq("""
            SELECT term.name,term.id FROM term
            INNER JOIN ontology
            ON term.ontology_id=ontology.id
            WHERE ontology.prefix='BTO';""")

    def generate():
        with open(path) as h:
            next(h)
            for line in h:
                gsm, _, bto_name = line.strip().split("\t")
                term_id = term_name_to_id.get(bto_name)
                sample_id = sample_accession_to_id.get(gsm)
                if (term_id is not None) and (sample_id is not None):
                    yield term_id,sample_id,1,evidence_id,source_id

    bulk_load_generator(generate(), "term_channel",
            "term_id","sample_id","channel","evidence_id","source_id")

######################################
# Text-mining based sample annotations
######################################

def group_if_match(pattern, group, text):
    m = re.search(pattern, text)
    if m:
        return m.group(group)

PATTERNS = {
    "age": "[^\w]age( *\((?P<age_unit1>[a-z]*)\))?:\
[ \t]*(?P<age>\d+[\.0-9]*)(( *\- *| (to|or) )\
(?P<age_end>\d+[\.\d]*))?([ \t]*(?P<age_unit2>[a-z]+))?",
    "age_unit": "(age\s*unit[s]*|unit[s]* of age): (?P<age_unit>[a-z])",
    # Tissue (TODO: map to BTO)
    "tissue": "(cell type|tissue|organ) *: *(?P<tissue>[A-Za-z0-9\+\- ]+)",
    # Disease states (TODO: map to DO)
    "cancer": "(tumor|tumour|cancer|sarcoma|glioma|leukem|mesothelioma|metastasis|carcinoma|lymphoma|blastoma|nsclc|cll|ptcl)",
    "infection": "infec"
}
PATTERNS = dict((k, re.compile(v)) for k,v in PATTERNS.items())

# A common additional unit is "dpc", which refers to embryos. 
# Currently ignored.
# Some samples are labeled with something like "11 and 14 weeks". 
# I have no idea what this means, so it's ignored. 
TIME_CONVERSION = {
        "year": 12,
        "y": 12,
        "yr": 12,
        "month": 1,
        "moth": 1, # yes...
        "mo": 1,
        "m": 1,
        "week": 1 / 4.5,
        "wek": 1 / 4.5, # ...
        "wk": 1 / 4.5,
        "w": 1 / 4.5,
        "day": 1 / 30,
        "d": 1 / 30,
        "hour": 1 / (24 * 30),
        "hr": 1 / (24 * 30),
        "h": 1 / (24 * 30)
}

def load_channel_age():
    cursor.execute("SELECT id FROM term WHERE name='age';")
    age_term_id = next(cursor)[0]
    rows = []
    evidence = "text mining"
    evidence_id = ensure_inserted_and_get_index(
            "evidence","name",[evidence])[evidence]
    source = "Wren Lab"
    source_id = ensure_inserted_and_get_index(
            "source", "name", [source])[source]

    cursor.execute("""
        SELECT st.id,taxon.id,st.text FROM sample_text st
        INNER JOIN sample
        ON sample.id=st.id
        INNER JOIN taxon
        ON sample.taxon_id=taxon.id;
        """)
    for sample_id,taxon_id,text in cursor:
        default_unit = "year" if taxon_id == 9606 else None
        m = re.search(PATTERNS["age"], text)
        if m is None:
            continue
        age = float(m.group("age"))
        age_end = m.group("age_end")
        if age_end:
            #if not use_age_range:
            #    continue
            age = (age + float(age_end)) / 2
        
        unit = group_if_match(PATTERNS["age_unit"], 
                "age_unit", text) \
                or m.group("age_unit2") \
                or m.group("age_unit1")
                #or default_unit
        if not unit:
            continue
        unit = unit.rstrip("s")
        if not unit in TIME_CONVERSION:
            continue
        conversion_factor = TIME_CONVERSION[unit]
        rows.append((age_term_id, sample_id, evidence_id, source_id,
                age * conversion_factor))
    bulk_load_generator(rows, "term_sample",
            "term_id","sample_id","evidence_id","source_id","value") 

##############################
# Load GEO probe & MiniML data
##############################

def read_ailun():
    platform_accession_to_id = mapq("SELECT accession,id FROM platform;")

    for i,path in enumerate(os.listdir(AILUN_DIR)):
        if not path.endswith(".annot.gz"):
            continue
        platform_accession = path.split(".")[0]
        platform_id = platform_accession_to_id.get(platform_accession)
        if not platform_id:
            continue
        path = os.path.join(AILUN_DIR, path)
        mappings = []
        with gzip.open(path, "rt") as h:
            for line in h:
                try:
                    probe_name, gene_id, *_ = line.split("\t")
                    gene_id = int(gene_id)
                    mappings.append((probe_name, gene_id))
                except:
                    pass
        LOG.debug("Processing platform %s" % platform_accession)
        yield platform_id, mappings

@QUEUE.task
def load_probe_from_accession(platform_id, platform_accession):
    GPL_DIR = "/data/public/ncbi/geo/gpl/"
    path = os.path.join(GPL_DIR, "%s-tbl-1.txt" % platform_accession)
    if not os.path.exists(path):
        return
    n = 0
    with open(path) as h:
        for line in h:
            n += 1
    if n > 500000:
        return
    def generate():
        with open(path) as h:
            for line in h:
                try:
                    probe_accession = line.split("\t")[0]
                    yield platform_id, probe_accession
                except:
                    pass
    bulk_load_generator(generate(), "probe", "platform_id", "accession")

@QUEUE.task
@populates(check_query="""
        SELECT *
        FROM probe
        LIMIT 1;""")
def load_probe():
    cursor.execute("SELECT id,accession FROM platform;")
    group(load_probe_from_accession.s(*r) for r in cursor)()

@cached
def get_genes():
    cursor.execute("SELECT id FROM gene;")
    return set([r[0] for r in cursor])

@QUEUE.task
def load_probe_gene_from_accession(platform_id, platform_accession):
    LOG.debug(platform_accession)
    AILUN_DIR = "/data/public/ncbi/geo/annotation/AILUN"
    path = os.path.join(AILUN_DIR, "%s.annot.gz" % platform_accession)
    if not os.path.exists(path):
        return
    probe_name_to_id = mapq("""
        SELECT accession,id FROM probe
        WHERE platform_id=%s;""" % platform_id)
    if len(probe_name_to_id) == 0:
        return

    def generate():
        with gzip.open(path, "rt") as h:
            for line in h:
                try:
                    probe_name, gene_id, *_ = line.split("\t")
                except Exception as e:
                    pass
                gene_id = int(gene_id)
                probe_id = probe_name_to_id.get(probe_name)
                if probe_id is None:
                    continue
                yield probe_id, gene_id
    bulk_load_generator(generate(), 
            "probe_gene", "probe_id", "gene_id")

@populates("probe_gene")
def load_probe_gene():
    cursor.execute("SELECT id,accession FROM platform;")
    jobs = list(cursor)
    group(load_probe_gene_from_accession.s(*r) for r in jobs)()

@QUEUE.task
def load_probe_data_from_archive(path):
    platform_accession = os.path.basename(path).split(".")[0]
    LOG.debug(platform_accession)
    cursor.execute("""
        SELECT probe.accession
        FROM probe
        INNER JOIN platform
        ON platform.id=probe.platform_id
        WHERE platform.accession=%s
        ORDER BY probe.id;""", (platform_accession,))
    try:
        probes = [r[0] for r in cursor]
    except Exception as e:
        print(e)
        return
    if len(probes) == 0:
        return
    probes = dict((a,i) for (i,a) in enumerate(probes))

    sample_accession_to_id = mapq("""
        SELECT sample.accession,sample.id
        FROM sample
        INNER JOIN platform
        ON sample.platform_id=platform.id
        WHERE platform.accession='%s';""" % (platform_accession,))

    NaN = float("NaN")
    n = 0
    with tarfile.open(path, "r:xz") as archive:
        for item in archive:
            if not (item.name.startswith("GSM") and \
                    item.name.endswith(".txt")):
                continue
            sample_accession = item.name.split("-")[0]
            sample_id = sample_accession_to_id.get(sample_accession)
            channel = int(item.name.split("-")[-1].rstrip(".txt"))
            if sample_id is None or channel not in [1,2]:
                continue
            with archive.extractfile(item) as h:
                data = np.zeros(len(probes))
                data[:] = np.nan
                lines = h.read().decode("utf-8").strip().split("\n")
                for line in lines:
                    try:
                        probe_accession, value, *_ = line.split("\t")
                    except ValueError:
                        continue
                    probe_index = probes.get(probe_accession)
                    if probe_index is None:
                        continue
                    try:
                        value = float(value)
                    except ValueError:
                        continue
                    data[probe_index] = value
                if np.isnan(data).all():
                    continue
                data = [float(x) if not np.isnan(x) else NaN for x in data]
                assert(len(data) == len(probes))
                cursor.execute("""
                    UPDATE channel
                    SET probe_data=%s
                    WHERE sample_id=%s AND channel=%s;
                    """, (data, sample_id, channel))
                n += 1

    LOG.debug("%s - %s datasets loaded" % (platform_accession, n))
    connection.commit()

@QUEUE.task
@populates(check_query="""
SELECT * FROM channel 
WHERE probe_data IS NOT NULL
LIMIT 1;""")
def load_probe_data():
    GEO_DIR = "/data/public/geo/miniml"
    paths = [os.path.join(GEO_DIR, name) for name in os.listdir(GEO_DIR)]
    paths.sort(key=os.path.getsize, reverse=True)
    group(load_probe_data_from_archive.s(path) for path in paths)()

def collapse_probe_data_for_platform(platform_id):
    LOG.debug(platform_id)
    cursor.execute("""
        SELECT taxon.id
        FROM taxon
        INNER JOIN channel
        ON channel.taxon_id=taxon.id
        INNER JOIN sample
        ON sample.id=channel.sample_id
        WHERE sample.platform_id=%s
        GROUP BY taxon.id
        ORDER BY count(taxon.id) DESC
        LIMIT 1;""", (platform_id,))
    taxon_id = next(cursor)[0]

    cursor.execute("""
        SELECT id
        FROM probe
        WHERE platform_id=%s
        ORDER BY id;""", (platform_id,))
    probes = [r[0] for r in cursor]

    cursor.execute("""
        SELECT id
        FROM gene
        WHERE taxon_id=%s
        ORDER BY id;""", (taxon_id,))
    genes = [r[0] for r in cursor]

    mask = pd.DataFrame(np.zeros((len(genes), len(probes))),
            index=genes, columns=probes)

    cursor.execute("""
            SELECT gene_id, probe_id
            FROM probe_gene
            INNER JOIN probe
            ON probe_gene.probe_id=probe.id
            WHERE probe.platform_id=%s
            ORDER BY probe_id;""", (platform_id,))
    for gene_id, probe_id in cursor:
        mask.loc[gene_id, probe_id] = 1
    n = np.array(mask.sum())
    mask = mask.as_matrix()
    print(n)
    print(mask)
    print(n.sum())
    print(mask.sum().sum())
    if True:
        return

    cursor.execute("""
        SELECT sample_id,channel,probe_data
        FROM channel
        INNER JOIN sample
        ON channel.sample_id=sample.id
        WHERE probe_data IS NOT NULL
        AND channel.taxon_id=%s
        AND sample.platform_id=%s""", 
        (taxon_id, platform_id,))
    for sample_id, channel, data in cursor:
        data = np.array(data)

        ix = annotation[data.index]
        mu = data.groupby(ix).mean().iloc[:,0]
        mu = mu + 1e-5 - mu.min()
        if mu.max() > 100:
            mu = mu.apply(np.log2)
        mu = (mu - mu.mean()) / mu.std()
        data = np.array(mu[genes])
        data = list(map(float, data))
        cursor.execute("""
            UPDATE channel
            SET gene_data=%s
            WHERE channel.sample_id=%s AND channel.channel=%s""",
            (data, sample_id, channel))
    connection.commit()

def collapse_probe_data():
    cursor.execute("SELECT id FROM platform;")
    platforms = [r[0] for r in cursor]
    for platform_id in platforms:
        collapse_probe_data_for_platform(platform_id)

# Text mining

from BioTK.io import MEDLINE

@populates("journal")
def load_journal():
    MEDLINE_DIR = "/data/public/ncbi/medline/"
    issn = set()
    nlm_id = set()
    def generate():
        for path in os.listdir(MEDLINE_DIR):
            if not path.endswith(".xml.gz"):
                continue
            path = os.path.join(MEDLINE_DIR, path)
            for article in MEDLINE.parse(path):
                journal = article.journal
                if journal.issn in issn:
                    continue
                if journal.id in nlm_id:
                    continue
                nlm_id.add(journal.id)
                issn.add(journal.issn)
                yield journal.id, journal.name, journal.issn
    bulk_load_generator(generate(), "journal",
            "nlm_id", "name", "issn")

@populates("publication")
def load_publication():
    journal_by_nlm_id = mapq("""
        SELECT nlm_id,id
        FROM journal
        WHERE nlm_id IS NOT NULL;""")
    MEDLINE_DIR = "/data/public/ncbi/medline/"
    def generate():
        ids = set()
        for path in os.listdir(MEDLINE_DIR):
            if not path.endswith(".xml.gz"):
                continue
            LOG.debug(path)
            for article in MEDLINE.parse(path):
                journal_id = journal_by_nlm_id.get(article.journal.id)
                if article.id in ids:
                    continue
                ids.add(article.id)
                yield journal_id, article.id, article.title, article.abstract
    bulk_load_generator(generate(), "publication", 
            "journal_id", "pubmed_id", "title", "abstract")

############
# CARPE DIEM
############

@populates(check_query="""
        SELECT * from term_term""")
def carpe_diem():
    pass

##########
# Indexing
##########

def ensure_index(table, columns, index_type):
    if len(columns) == 1 and "to_tsvector" in columns[0]:
        name = "_".join([table] + ["to_tsvector"] + ["idx"])
    else:
        name = "_".join([table] + list(columns) + ["idx"])

    index = "%s (%s)" % (table, ", ".join(columns))
    try:
        cursor.execute("SELECT 'public.%s'::regclass" % name)
        LOG.info("Index exists: %s" % name)
    except psycopg2.ProgrammingError:
        connection.rollback()
        LOG.info("Creating index on %s" % index)
        cursor.execute("CREATE INDEX ON %s USING %s(%s);" % \
                (table, index_type, ", ".join(columns)))
    connection.commit()

indexes = {
    "gin": [
        ("taxon", "name"),
        ("gene", "symbol", "name"),
        ("series", "title", "summary", "design"),
        ("sample", "title", "source_name", "description", "characteristics"),
        ("term", "name"),
    ],
    "btree": [
        ("sample", "taxon_id"),
        ("sample", "platform_id"),
        ("probe", "platform_id"),
        ("term", "ontology_id"),
        ("term_gene", "term_id"),
        ("term_gene", "gene_id"),
        ("term_sample", "term_id"),
        ("term_sample", "sample_id")
    ]
}

def tsvec(*columns):
    return "to_tsvector('english', (%s))" % " || ' ' || ".join(columns)

def index_all():
    for type, ixs in indexes.items():
        for table, *columns in ixs:
            if type == "gin":
                columns = tsvec(*columns)
            ensure_index(table, columns, type)

######
# Main
######

from celery.signals import worker_process_init

@worker_process_init.connect
def initialize(*args, **kwargs):
    global connection, cursor
    connection = connect()
    c = cursor = connection.cursor()
