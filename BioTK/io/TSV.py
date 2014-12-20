__all__ = ["read_matrix", "read_factor", "read_vector", "read_sparse_matrix"]

import sys
import multiprocessing as mp
from collections import defaultdict

import numpy as np
import pandas as pd

from BioTK.matrix import MatrixIterator
from . import as_float

def _split_line(line, delimiter="\t"):
    return line.strip("\n").split(delimiter)

columns = None
as_array = False
delimiter = None
def _read_matrix_item_init(columns_, as_array_, delimiter_):
    global columns, as_array, delimiter
    delimiter = delimiter_
    columns = columns_
    as_array = as_array_

def _read_matrix_item(line):
    global columns, as_array
    key, *data = _split_line(line, delimiter=delimiter)
    #assert len(data) == len(columns)
    data = np.fromiter(data, np.float64)
    if as_array:
        return key, data
    else:
        x = pd.Series(data, index=columns, dtype=float)
        x.name = key
        return x

def read_matrix(handle=sys.stdin, as_array=False, 
        header=True, delimiter="\t"):
    columns = None
    if header:
        columns = _split_line(next(handle), 
                delimiter=delimiter)[1:]
        columns = pd.Index(columns)
    p = mp.Pool(initializer=_read_matrix_item_init, 
            initargs=(columns,as_array,delimiter))
    rows = p.imap(_read_matrix_item, handle)

    return MatrixIterator(rows, header=header, 
            columns=columns)

def read_sparse_matrix(handle, delimiter="\t"):
    """
    Read a sparse matrix in "COO" format and return
    as a pandas SparseDataFrame.

    The format has 2-3 columns:
        1: row label (required)
        2: column label (required)
        3: value (optional; defaults to 1)
    """
    data = defaultdict(dict)
    with handle:
        for line in handle:
            r,*c = _split_line(line, delimiter=delimiter)
            v = as_float(c[1]) if len(c) == 2 else 1
            c = c[0]
            data[r][c] = v

    ix = list(data.keys())
    ss = []
    for r in ix:
        vs = data[r]
        ss_ix = list(vs.keys())
        ss.append(pd.SparseSeries([vs[k] for k in ss_ix],
            index=ss_ix))

    return pd.DataFrame(ss, index=ix).to_sparse()

def read_factor(handle, delimiter="\t"):
    data = {}
    with handle:
        for line in handle:
            try:
                key, value = _split_line(line,
                                         delimiter=delimiter)
            except:
                raise ValueError("Factor format can only contain two values per line")
            data[key] = value
    return pd.Series(data)

def read_vector(handle, delimiter="\t"):
    data = {}
    with handle:
        for line in handle:
            try:
                key, value = _split_line(line,
                                         delimiter=delimiter)
            except:
                raise ValueError("Factor format can only contain two values per line")
            data[key] = as_float(value)
    return pd.Series(data)
