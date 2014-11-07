import os
import tempfile
import sys

import pickle
import numpy as np
import pandas as pd
import tc
import lz4

from BioTK.matrix import MatrixIterator

def as_float(x):
    try:
        return float(x)
    except ValueError:
        return np.nan

class Metadata(object):
    def __init__(self, store, auto_sync=False):
        self.store = store
        try:
            self.store._db.get("_meta")
        except KeyError:
            self.store._db.put("_meta", pickle.dumps({}))
        self._auto_sync = auto_sync
        self.sync()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        if self._auto_sync:
            self.sync()

    def sync(self):
        if hasattr(self, "_data") and "w" in self.store.mode:
            serialized = pickle.dumps(self._data)
            self.store._db.put(b"_meta", serialized)
        self._data = pickle.loads(self.store._db.get("_meta"))

class Index(object):
    def __init__(self, store, axis):
        assert axis in (0,1)
        self.store = store
        self.axis = axis

    def __getitem__(self, key):
        key = ("%s_%s" % (self.axis, key))
        data = np.fromstring(lz4.loads(self.store._db.get(key)),
                             dtype=np.float64)
        index_key = "columns" if self.axis==0 else "index"
        index = self.store._meta[index_key]
        x = pd.Series(data, index=index)
        x.name = key[2:]
        return x

    def __iter__(self):
        prefix = ("%s_" % self.axis).encode("utf-8")
        for key in self.store._db.keys():
            if key.startswith(prefix):
                key = key.decode("utf-8")[2:]
                yield self.__getitem__(key)

class MatrixStore(MatrixIterator):
    def __init__(self, path, mode="rw", columns=None):
        self._db = tc.HDB()
        self.mode = mode
        new = not os.path.exists(path)
        if "w" in mode:
            mode_flags = tc.HDBOWRITER | tc.HDBOCREAT
        elif "r" in mode:
            mode_flags = tc.HDBOREADER | tc.HDBONOLCK
        else:
            raise ValueError("Invalid value for mode: must be 'rw' or 'r'")
        self._db.open(path, mode_flags)
        self._meta = Metadata(self)

        if new:
            assert columns is not None
            self._meta["columns"] = list(columns)
            self._meta["rows"] = []

    def close(self):
        self._meta.sync()
        self._db.close()

    def __del__(self):
        self.close()

    ##########
    # Main API
    ##########

    @property
    def rows(self):
        return Index(self, 0)

    @property
    def columns(self):
        return Index(self, 1)

    def _get(self, key):
        if isinstance(key, bytes):
            key = key.decode("utf-8")
        assert key != "_meta"
        data = np.fromstring(lz4.loads(self._db.get(key)),
                             dtype=np.float64)
        x = pd.Series(data, index=self._columns)
        x.name = key
        return x

    def _set(self, key, values):
        #assert len(values) == len(self._meta["columns"])
        assert key != "_meta"

        data = np.array(values, dtype=np.float64)
        self._db.put(key, lz4.dumps(data.tostring()))

    def __iter__(self):
        return iter(self.rows)

    @staticmethod
    def load(handle, path):
        if os.path.exists(path):
            raise FileExistsError

        # First index by row
        print("Indexing rows ...", file=sys.stderr)
        index = []
        with handle:
            columns = next(handle).strip("\n").split("\t")[1:]
            store = MatrixStore(path, columns=columns, mode="rw")
            for i,line in enumerate(handle):
                if i and (i % 1000 == 0):
                    print("*", i, file=sys.stderr)
                key, *data = line.strip("\n").split("\t")
                index.append(key)
                data = list(map(as_float, data))
                key = "0_%s" % key
                store._set(key, data)

        store._meta.sync()

        from subprocess import Popen, PIPE
        # Index by column
        print("Indexing columns ...", file=sys.stderr)
        o = tempfile.NamedTemporaryFile()
        p = Popen(["transpose"], stdin=PIPE, stdout=o,
                  universal_newlines=True)
        with p.stdin:
            store.dump(handle=p.stdin)
        p.wait()

        with open(o.name) as handle:
            next(handle)
            for i,line in enumerate(handle):
                if i and (i % 1000 == 0):
                    print("*", i, file=sys.stderr)
                key, *data = line.strip("\n").split("\t")
                data = list(map(as_float, data))
                key = "1_%s" % key
                store._set(key, data)
        store._meta["index"] = index
        store._meta.sync()
        return store

        """
        index = store._meta["index"] = \
            list(r.name for r in store)
        rows = store.rows
        columns = store._meta["columns"]
        step = 100
        for start in range(0, len(columns), step):
            end = min(start + step, len(columns))
            print("*", start, "-", end, file=sys.stderr)
            cs = [columns[i] for i in range(start, end)]
            data = zip(*[rows[ix][cs] for ix in index])
            for c, v in zip(cs, data):
                key = "1_%s" % c
                store._set(key, v)

        store._meta.sync()
        return store
        """

#####
# CLI
#####

import click

@click.group()
def cli():
    pass

@cli.command(help="Load input data into an indexed matrix file")
@click.argument("path")
def load(path):
    MatrixStore.load(sys.stdin, path)

@cli.command(help="Dump matrix data to stdout")
@click.argument("path")
@click.option("--delimiter", "-d", default="\t")
def dump(path, delimiter):
    store = MatrixStore(path, mode="r")
    store.dump(delimiter=delimiter)

@cli.command(help="Output one row or column from the matrix in a key-value format")
@click.argument("path")
@click.argument("key")
@click.option("--column/--row", "-c", default=False)
@click.option("--all/--filter-na", "-a", default=False)
def get(path, key, column, all):
    store = MatrixStore(path, mode="r")

    if column:
        data = store.columns[key]
    else:
        data = store.rows[key]
    items = zip(data.index, data)

    for label, value in items:
        if np.isnan(value) and not all:
            continue
        print(label, value, sep="\t")

if __name__ == "__main__":
    cli()
