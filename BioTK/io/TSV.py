__all__ = [
    "read_matrix", 
    "read_factor", 
    "read_vector", 
    "read_multimap",
    "read_sparse_matrix", 
]

import sys
from collections import defaultdict

import numpy as np
import pandas as pd

from BioTK.matrix import MatrixIterator
from BioTK.util import MultiMap
from . import as_float

def _split_line(line, delimiter="\t"):
    return line.strip("\n").split(delimiter)

def read_matrix(handle=sys.stdin, 
        as_array=False, 
        eager=False,
        header=True, 
        delimiter="\t"):
    """
    Read a text delimited matrix from a handle, returning 
    either a :class:`BioTK.matrix.MatrixIterator` 
    (if eager=False, the default), or a :class:`pandas.DataFrame`
    if eager=True.
    """

    if eager is True:
        return pd.read_table(handle, sep=delimiter, header=header)

    columns = None
    if header:
        columns = _split_line(next(handle), 
                delimiter=delimiter)[1:]
        columns = pd.Index(columns)

    def read_rows():
        for line in handle:
            key, *data = _split_line(line, delimiter=delimiter)
            data = np.fromiter(data, np.float64)
            if as_array:
                yield key, data
            else:
                x = pd.Series(data, index=columns, dtype=float)
                x.name = key
                yield x

    rows = read_rows()
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

def read_multimap(handle, 
        key_type=str, value_type=str,
        delimiter="\t"):
    data = MultiMap()
    for line in handle:
        try:
            k,v = _split_line(line,delimiter=delimiter)
        except:
            raise ValueError("Multimap format can only contain two values per line")
        try:
            k = key_type(k)
            v = value_type(v)
        except:
            raise ValueError("Line not conforming to key_type or value_type: %s" % line)
        data[k].add(v)
    return data
