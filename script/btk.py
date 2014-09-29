import os
import sys
import gzip
import multiprocessing as mp
import functools

import psycopg2
import numpy as np
import yaml
import pandas as pd

# Don't throw broken pipe error
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)

# Ignore malformed UTF-8
#import codecs
#sys.stdin = codecs.getreader("utf8")(sys.stdin.detach(), errors="replace")

def parse_float(x):
    try:
        return float(x)
    except ValueError:
        return np.nan

class FieldReader(object):
    def __init__(self, file=sys.stdin, delimiter="\t"):
        path_or_handle = file
        self.delimiter = delimiter
        if isinstance(path_or_handle, str):
            path = path_or_handle
            if path.endswith(".gz"):
                self.handle = gzip.open(path, "rt")
            else:
                self.handle = open(path)
        elif hasattr(path_or_handle, "read"):
            self.handle = path_or_handle

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.handle.close()

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.handle).strip("\n").replace("\x00","").split(self.delimiter)

# FIXME: output series
class MatrixReader(FieldReader):
    def __init__(self, *args, header=True,
            **kwargs):
        self.header = header
        super(MatrixReader, self).__init__(*args)

    def __next__(self):
        fields = super(MatrixReader, self).__next__()
        if self.header:
            self.header = False
            return fields
        name, *data = fields
        data = np.array(list(map(parse_float, data)))
        return name, data

def map_over_matrix(fn, handle=None):
    if handle is None:
        path_or_handle = sys.argv[1] if len(sys.argv) > 1 else sys.stdin
    else:
        path_or_handle = handle

    handle = path_or_handle
    header = next(handle).strip("\n")
    print(header)
    columns = header.split("\t")[1:]

    p = mp.Pool()
    for name, rs in p.imap_unordered(fn, handle):
        if rs is not None:
            print(name, *rs, sep="\t")

def matrix_map(fn):
    @functools.wraps(fn)
    def wrap(line):
        name, *fields = line.strip("\n").split("\t")
        x = pd.Series(list(map(parse_float, fields)))
        return fn(name, x)

    def run(handle=None):
        map_over_matrix(wrap, handle=handle)

    wrap.run = run
    return wrap

def index_positions(items):
    return dict(map(reversed, enumerate(items)))

def get_configuration():
    path = os.path.expanduser("~/.BioTK.yml")
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__),
                "..", "etc", "BioTK.yml")
    with open(path) as h:
        return yaml.load(h)

def get_connection():
    cfg = get_configuration()["database"]
    return psycopg2.connect(
            host=cfg["host"],
            dbname=cfg["name"],
            port=cfg["port"])

def read_table(file=sys.stdin, **kwargs):
    if isinstance(file, str):
        compression = "gzip" if file.endswith(".gz") else None
    return pd.read_table(file, **kwargs)
