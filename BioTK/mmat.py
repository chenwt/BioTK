__all__ = ["MemoryMappedMatrix", "MMAT"]

import collections
import os
import pickle
import subprocess as sp
import sys
import warnings
import itertools
import time

from functools import partialmethod

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

def format_message(msg):
    return "\n".join([line.strip() for line in msg.split("\n")
        if line.strip()])

def as_float(x):
    try:
        return float(x)
    except ValueError:
        return np.nan

def chunks(it, size=1000):
    """
    Divide an iterator into chunks of specified size. A
    chunk size of 0 means no maximum chunk size, and will
    therefore return a single list.
    
    Returns a generator of lists.
    """
    if size == 0:
        yield list(it)
    else:
        chunk = []
        for elem in it:
            chunk.append(elem)
            if len(chunk) == size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

HeaderType = np.dtype([
    ("magic", np.int64),
    ("version", np.int32),
    ("n_rows", np.int64),
    ("n_columns", np.int64),
    ("max_rows", np.int64),
    ("max_columns", np.int64),
    ("dtype_length", np.int64),
    ("loading_time", np.float32),
    ("reserved", "S65")
])

StringType = np.dtype("U100")

def slice_to_array(sl, length):
    start = sl.start or 0
    stop = sl.stop or length
    step = sl.step or 1
    return np.arange(start, stop, step)

def fix_index(ix):
    if ix is None:
        return None
    elif ix.dtype == np.object:
        ix = list(map(str, ix))
        dtype = StringType
    else:
        dtype = ix.dtype
    assert len(ix) == len(set(ix)), "duplicate elements in row or column names are not allowed."
    return np.array(ix, dtype=dtype)

class IndexedMmap(np.memmap):
    def __init__(self, *args, **kwargs):
        super(IndexedMmap, self).__init__()
        self._ix = {}
        self._make_index()

    def _make_index(self):
        unique_elements = set(k for k,v in collections.Counter(self).items() \
                if v==1)
        self._ix = dict((v,i) for (i,v) in enumerate(self) \
                if v in unique_elements)
    
    def _get_locs(self, arg):    
        if isinstance(arg, slice):
            # A slice of index elements
            return True, slice_to_array(arg, self.shape[0])
        elif isinstance(arg, str):
            # A single string item
            return False, self._ix[arg]
        elif hasattr(arg, "__iter__"):
            # A collection of index elements
            return True, [self._ix[e] for e in arg]
        else:
            # A single item
            return False, self._ix[arg]

    def __setitem__(self, *args, **kwargs):
        super(IndexedMmap, self).__setitem__(*args, **kwargs)
        self._make_index()

class Indexer(object):
    def __init__(self, index, columns, data):
        self._index = index
        self._columns = columns
        self._data = data

    def __getitem__(self, slices):
        row_ix, col_ix = slices
        row_multi, row_ix = self._index._get_locs(row_ix)
        col_multi, col_ix = self._columns._get_locs(col_ix)
        if (not row_multi) and (not col_multi):
            return self._data[row_ix,col_ix]
        elif row_multi and col_multi:
            return View(self._index[row_ix], self._columns[col_ix],
                    self._data[row_ix,:][:,col_ix])
        elif row_multi:
            return pd.Series(self._data[row_ix,:][:,col_ix], 
                    index=self._index[row_ix],
                    name=self._columns[col_ix])
        elif col_multi:
            return pd.Series(self._data[row_ix,:][col_ix],
                    index=self._columns[col_ix],
                    name=self._index[row_ix])

class View(object):
    def __init__(self, index, columns, data):
        self.index = index
        self.columns = columns
        self.data = data

    @property
    def shape(self):
        return (self.index.shape[0], self.columns.shape[0])

    @property
    def loc(self):
        return Indexer(self.index, self.columns, self.data)

    def head(self):
        n = min(10, self.shape[0])
        return View(self.index[:n], self.columns, self.data[:n,:])

    def __repr__(self):
        return self.data.__repr__()

    def to_frame(self):
        """
        Return this View as an (in-RAM) pandas.DataFrame.
        """
        return pd.DataFrame(self.data, 
                index=self.index, 
                columns=self.columns)

    def corrwith(self, series):
        assert (series.index == self.columns).all()
        series_nan = np.isnan(series)
        o = np.zeros(self.shape[0])
        o[:] = np.nan
        for i in range(self.shape[0]):
            x = self.data[i,:]
            ix = ~(series_nan | np.isnan(x))
            if ix.sum() > (0.25 * len(series)):
                o[i] = pearsonr(series.loc[ix], x[ix.nonzero()])[0]
        name = series.name or None
        return pd.Series(o, index=self.index, name=name)

    ############
    # Reductions
    ############

    # Unlike accessing View.data directly, these mask nans
    # and return pandas.Series objects 

    def reduce(self, reduce_fn, sample=None, 
            ignore_na=True, axis=0):
        assert axis in (0,1)

        if axis == 0:
            gen = (self.data[i,:] for i in range(self.shape[0]))
            ix = self.index
        else:
            gen = (self.data[:,j] for j in range(self.shape[1]))
            ix = self.columns
        o = np.empty(ix.shape[0])
        o[:] = np.nan
        for i,x in enumerate(gen):
            if ignore_na:
                mask = ~np.isnan(x)
            else:
                mask = np.ones(len(x)).astype(bool)
            if mask.sum() > 1:
                o[i] = reduce_fn(x[mask])
        return pd.Series(o, index=ix)

    def to_tsv(self, transpose=False, 
            delimiter="\t",
            file=sys.stdout):
        # FIXME: implement index.name and columns.name
        print(delimiter, end="", file=file)
        if not transpose:
            print(*self.columns, sep=delimiter, file=file)
            for i in range(self.shape[0]):
                print(self.index[i], *self.data[i,:], 
                        sep=delimiter, file=file)
        else:
            print(*self.index, sep=delimiter, file=file)
            for j in range(self.shape[1]):
                print(self.columns[j], *self.data[:,j],
                        sep=delimiter, file=file)

reductions = ["sum", "mean", "std", "var"]
for k in reductions:
    setattr(View, k, partialmethod(View.reduce, getattr(np, k)))

class MemoryMappedMatrix(View):
    """
    A simple wrapper for a 2D memory-mapped matrix with row and column IDs 
    (must be fixed-width numpy dtypes).

    The memory layout is as follows:

        byte 0-63: header, consisting of:
            byte 0-7: magic number (int64 : 0x11da549e21c7ef21)
            byte 8-12: file format version number (int32)
            byte 13-21: number of rows (int64)
            byte 22-30: number of columns (int64)
            byte 31-39: maximum number of rows (int64)
            byte 40-48: maximum number of columns (int64)
            byte 49-57: length of pickled dtype data (int64)
            byte 58-62: loading time in seconds (float32)
            byte 63-128: reserved for future expansion

        byte 129-??: pickled dtype data 
            A pickled tuple of 3 dtype objects, 
                corresponding the the dtypes of the 
                index, columns, and data. The length of 
                this byte string is specified in the header.

        byte ??-??: row index data of length equal to the 
            maximum number of rows * index dtype size
        byte ??-??: column index data of length equal to the 
            maximum number of columns * column dtype size
        byte ??-??: matrix data of size equal to the data dtype 
            * number of rows * number of columns
    """

    MAGIC_NUMBER = 0x11da549e21c7ef21
    DTYPE_OFFSET = HeaderType.itemsize

    def __init__(self, path, 
            shape=(0,0), max_shape=(1000000,1000000), 
            dtype=np.float32, 
            exclusive=False,
            index=None, columns=None,
            index_dtype=np.int64, columns_dtype=np.int64):
        """
        - exclusive : This object will be the exclusive owner 
            of the memory map. This is required if you want 
            to resize the array.
        """
        # FIXME: use portalock.lock(handle, LOCK_EX) if exclusive
        # (but requires to keep a handle around)
        self._exclusive = exclusive

        try:
            vmem = sp.check_output("ulimit -v", shell=True).strip()
            vmem = np.inf if vmem==b"unlimited" else int(vmem)
        except Exception as e:
            msg = format_message("""
            Failed to determine OS virtual memory limit
            (command 'ulimit -v' failed). If your OS is not 
            configured with a sufficiently large virtual memory 
            limit, mapping may fail. For best results,
            set this value to unlimited in your platform's
            equivalent of /etc/security/limits.conf""")
            warnings.warn(msg)
            # Proceed as though we have unlimited virtual memory
            vmem = np.inf

        self._path = path
        create = not os.path.exists(path)

        if create:
            self._map_header(create=True)
            index_data = fix_index(index)
            columns_data = fix_index(columns)
            shape = list(shape)
            if index_data is not None:
                shape[0] = len(index_data)
            if columns_data is not None:
                shape[1] = len(columns_data)

            self._header["magic"] = self.MAGIC_NUMBER
            self._header["n_rows"] = shape[0]
            self._header["n_columns"] = shape[1]
            self._header["max_rows"] = max_shape[0]
            self._header["max_columns"] = max_shape[1]

            if index_data is not None:
                index_dtype = index_data.dtype
            if columns_data is not None:
                columns_dtype = columns_data.dtype
            dtypes = (index_dtype, columns_dtype, dtype)
            dtype_str = pickle.dumps(dtypes)
            self._header["dtype_length"] = len(dtype_str)
            with open(path, "rb+") as h:
                h.seek(self.DTYPE_OFFSET)
                h.write(dtype_str)

        self.refresh()

        if create:
            if index_data is not None:
                self.index[:] = index_data
            if columns_data is not None:
                self.columns[:] = columns_data
        
    def _map_header(self, create=False):
        self._header_map = np.memmap(self._path, 
                mode="w+" if create else "r+", 
                shape=(1,), 
                dtype=HeaderType)
        self._header = self._header_map[0]

    def describe(self, file=sys.stdout):
        print("loading time\t%0.3f s" 
                % self._header["loading_time"])
        print("rows", self.shape[0], sep="\t")
        print("columns", self.shape[1], sep="\t")
        print("dtype", str(self.data.dtype), sep="\t")
        print("index dtype", str(self.index.dtype), sep="\t")
        print("columns dtype", str(self.columns.dtype), sep="\t")

    def refresh(self):
        self._map_header()
        nrow = self._header["n_rows"]
        ncol = self._header["n_columns"]

        assert self._header["magic"] == self.MAGIC_NUMBER, \
                "File '%s' is not a valid MemoryMappedMatrix file."

        with open(self._path, "rb") as h:
            h.seek(self.DTYPE_OFFSET)
            index_dtype, columns_dtype, dtype = \
                pickle.loads(h.read(self._header["dtype_length"]))

        self._index_offset = \
            self.DTYPE_OFFSET + self._header["dtype_length"]
        index = IndexedMmap(self._path, 
                mode="r+", offset=self._index_offset, 
                shape=(nrow,), dtype=index_dtype)

        self._columns_offset = self._index_offset + \
                np.dtype(index_dtype).itemsize * self.max_shape[0]
        columns = IndexedMmap(self._path, 
                mode="r+", offset=self._columns_offset, 
                shape=(ncol,), dtype=columns_dtype)

        self._data_offset = self._columns_offset + \
            np.dtype(columns_dtype).itemsize * self.max_shape[1]
        data = np.memmap(self._path, 
                mode="r+", offset=self._data_offset, 
                shape=(nrow, ncol), dtype=dtype)

        self.dtype = dtype
        super(MemoryMappedMatrix, self)\
                .__init__(index, columns, data)

    @property
    def max_shape(self):
        return (self._header["max_rows"], 
                self._header["max_columns"])

    def resize(self, shape):
        assert self._exclusive

        nrow, ncol = shape
        assert nrow <= self.max_shape[0]
        assert ncol <= self.max_shape[1]

        self._header["n_rows"] = nrow
        self._header["n_columns"] = ncol

        self.refresh()

        self.index._make_index()
        self.columns._make_index()

    def flush(self):
        self._header_map.flush()
        self.data.flush()
        self.index.flush()
        self.columns.flush()

    def __del__(self):
        self.flush()


    @staticmethod
    def from_file(handle, path, delimiter="\t"):
        chunk_size = 100
        growth_factor = 2
        start_time = time.time()

        def maybe_int(items):
            try:
                items = list(map(int, items))
            except ValueError:
                pass
            return pd.Index(items)

        with handle:
            columns = maybe_int(next(handle)\
                    .rstrip("\n").split(delimiter)[1:])
            nc = len(columns)
            #cnks = chunks(handle, chunk_size)
            #chunk = next(cnks)
            line = next(handle)
            try:
                int(line.split(delimiter)[0])
                index_dtype = np.int64
            except ValueError:
                index_dtype = StringType
            lines = itertools.chain([line], handle)

            X = MMAT(path, 
                    shape=(100, len(columns)),
                    dtype=np.float32,
                    max_shape=(1000000,nc),
                    exclusive=True,
                    index_dtype=index_dtype,
                    columns=columns)

            print(X.shape)
            index = []

            nr = 0
            for nr,line in enumerate(lines):
                if nr + 1 > X.shape[0]:
                    X.resize((int(X.shape[0]*growth_factor), 
                        nc))
                    print(X.shape, nr, nc)
                isep = line.find(delimiter)
                index.append(line[:isep])
                X.data[nr,:] = np.fromstring(line[isep+1:], 
                        sep=delimiter)

            X.resize((nr+1,nc))
            X.index[:] = fix_index(maybe_int(index))
            X._header["loading_time"] = time.time() - start_time
            return X

MMAT = MemoryMappedMatrix

########################
# Command-line interface
########################

import click

@click.group()
def cli():
    pass

@cli.command()
@click.argument("matrix_path", required=True)
@click.option("--delimiter", "-d", default="\t")
def load(matrix_path, delimiter="\t"):
    """
    Create a MMAT from TSV matrix
    """
    import sys
    X = MMAT.from_file(sys.stdin, matrix_path, delimiter=delimiter)
    start = time.time()
    e = lambda *args: print(*args, file=sys.stderr)
    e("\nMatrix loaded:")
    X.describe()

@cli.command()
@click.argument("matrix_path", required=True)
@click.option("--delimiter", "-d", default="\t")
@click.option("--transpose/--no-transpose", "-t", default=False)
def dump(matrix_path, delimiter="\t", transpose=False):    
    """
    Export a matrix's data to TSV
    """
    X = MMAT(matrix_path)
    X.to_tsv(delimiter=delimiter, transpose=transpose)

@cli.command()
@click.argument("matrix_path", required=True)
def describe(matrix_path, delimiter="\t"):    
    """
    Print MMAT shape, dtype, etc
    """
    X = MMAT(matrix_path)
    X.describe()

@cli.command()
@click.argument("matrix_path", required=True)
@click.argument("reduction", required=True)
@click.option("--axis", "-a", type=int, default=0)
def reduce(matrix_path, reduction, axis=0):
    """
    Reduce the matrix along an axis
    """
    X = MMAT(matrix_path)
    fn = getattr(np, reduction)
    X.reduce(fn, axis=axis)\
            .to_csv(sys.stdout, sep="\t", na_rep="nan")

@cli.command()
@click.argument("matrix_path", required=True)
@click.option("--ignore-missing", "-i",
        help="Don't throw an error if a label is missing, just omit it",
        is_flag=True)
@click.option("--rows", "-r", 
        help="Input lines are row labels (default)",
        is_flag=True)
@click.option("--columns", "-c", 
        help="Input lines are column labels",
        is_flag=True)
def select(matrix_path, rows, columns, ignore_missing):
    """
    Select rows or columns by key
    """
    if not rows or columns:
        rows = True
    assert (rows != columns), "-r and -c are mutually exclusive"
    X = MMAT(matrix_path)
    selection = [line.rstrip("\n") for line in sys.stdin]
    if ignore_missing:
        ix = set(X.index if rows else X.columns)
        selection = [x for x in selection if x in ix]
    if rows:
        X.loc[selection,:].to_tsv()
    else:
        X.loc[:,selection].to_tsv()

@cli.command()
@click.argument("matrix_path", required=True)
@click.option("--rows", "-r", is_flag=True)
@click.option("--columns", "-c", is_flag=True)
def keys(matrix_path, rows, columns):
    """
    Output row or column names
    """
    if not rows or columns:
        rows = True
    assert (rows != columns), "-r and -c are mutually exclusive"
    X = MMAT(matrix_path)
    if rows:
        keys = X.index
    else:
        keys = X.columns
    for k in keys:
        print(k)
 
if __name__ == "__main__":
    cli()

def test():
    X = MemoryMappedMatrix("/home/gilesc/test.mmat", shape=(10,10))
    X.columns[:] = np.arange(10) 
    X.index[:] = np.arange(10) 
    print(dir(X.data))

    print(X.loc[3:6,3])
    X.resize((20,20))
    print(X)
