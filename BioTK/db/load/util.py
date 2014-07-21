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

import bottleneck
import numpy as np
import pandas as pd
import psycopg2
from celery import group
from celery.signals import worker_process_init

from BioTK import LOG, CONFIG, CACHE_DIR
from BioTK.cache import cached, download
from BioTK.io import OBO
from BioTK.db import connect
import BioTK.util

from BioTK.task import QUEUE

#############
# Environment
#############

@worker_process_init.connect
def initialize(*args, **kwargs):
    global connection, cursor
    connection = connect()
    c = cursor = connection.cursor()

initialize()

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
    with tempfile.NamedTemporaryFile("wt", dir="/home/gilesc/.cache/") as h:
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
            else:
                LOG.info("Skipping %s" % fn.__name__)
            connection.commit()
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
    db_path = os.path.join(CACHE_DIR, "GEOmetadb.sqlite")
    if not os.path.exists(db_path):
        gz_path = download("http://gbnci.abcc.ncifcrf.gov/geo/GEOmetadb.sqlite.gz")
        with gzip.open(gz_path, "rb") as h_in:
            with open(db_path, "wb") as h_out:
                while True:
                    data = h_in.read(4096)
                    if not data:
                        break
                    h_out.write(data)
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

##########
# Indexing
##########

def ensure_index(table, columns, index_type="btree"):
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
        #("sample", "title", "source_name", "description", "characteristics"),
        ("term", "name"),
    ],
    "btree": [
        ("channel", "taxon_id"),
        ("sample", "platform_id"),
        ("gene", "taxon_id"),
        ("probe", "platform_id"),
        ("term", "ontology_id"),
        ("term_gene", "term_id"),
        ("term_gene", "gene_id"),
        ("term_channel", "term_id"),
        ("term_channel", "sample_id", "channel")
    ]
}

def tsvec(*columns):
    return ["to_tsvector('english', (%s))" % " || ' ' || ".join(columns)]

def index_all():
    for type, ixs in indexes.items():
        for table, *columns in ixs:
            if type == "gin":
                columns = tsvec(*columns)
            ensure_index(table, columns, type)

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
