import os
import io
import tarfile
import gzip
import sqlite3
import glob
import datetime

from collections import namedtuple
import multiprocessing as mp

import pandas as pd
from py2neo import neo4j, cypher, node, rel
from celery import group

import BioTK.io
from BioTK import LOG, CONFIG
from BioTK.io import MEDLINE, OBO

from . import BatchProxy
from ..util import *



##############
# Entry points
##############

def load_all(db):
    for label in [
            # Nodes
            "taxon"]:
            #"gene",
            #"ontology", "term", "synonym", #"term_term",
            #"journal", #"publication", 
            #"platform", "series", "sample",
            # Mappings
            #"gene_go", "sample_bto"
            #]:
        loader = globals()["load_"+label]
        if label_exists(label):
            LOG.info("[%s] No insert required" % label)
        else:
            LOG.info("[%s] Begin processing" % label)
            batch = BatchProxy(db)
            rs = loader(db, batch)
            if rs is False:
                LOG.info("[%s] No insert required" % label)
            batch.run()

def main():
    db = neo4j.GraphDatabaseService()
    mp.set_start_method("spawn")
    load_all(db)

if __name__ == "__main__":
    main()
