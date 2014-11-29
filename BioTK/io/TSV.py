__all__ = ["read_matrix", "read_factor", "read_vector"]

import pandas as pd

from BioTK.matrix import MatrixIterator
from . import as_float

def _split_line(line, delimiter="\t"):
    return line.strip("\n").split(delimiter)

def read_matrix(handle, header=True, delimiter="\t"):
    columns = None
    if header:
        columns = _split_line(next(handle), delimiter=delimiter)[1:]
        columns = pd.Index(columns)
    def generate():
        for line in handle:
            key, *data = _split_line(line, delimiter=delimiter)
            #assert len(data) == len(columns)
            data = list(map(as_float, data))
            x = pd.Series(data, index=columns)
            x.name = key
            yield x
    return MatrixIterator(generate(), header=header)

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
