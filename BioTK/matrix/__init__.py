import itertools
import sys

import numpy as np
import pandas as pd

class MatrixIteratorBase(object):
    def __init__(self, rows, columns=None, header=True):
        # rows must be a sequence of pandas Series
        self.rows = iter(rows)
        self.header = header
        self.columns = columns

    def dump(self, handle=sys.stdout, delimiter="\t", precision=3):
        rows = iter(self)
        if self.header:
            if self.columns is not None:
                print("", *self.columns, sep=delimiter, file=handle)
            else:
                row = next(rows)
                print("", *row.index, sep=delimiter, file=handle)
                rows = itertools.chain([row], rows)
        fmt = "{0:0." + str(precision) + "f}"
        for row in rows:
            data = list(map(fmt.format, row))
            print(row.name, *data, sep=delimiter, file=handle)

    def apply(self, fn, **kwargs):
        def generator():
            for row in self:
                rs = fn(row, **kwargs)
                if rs is not None:
                    yield rs
        return MatrixIterator(generator(), header=self.header)

    def to_frame(self):
        return pd.DataFrame(self.rows, columns=self.columns)

class MatrixIterator(MatrixIteratorBase):
    def __iter__(self):
        # Override in subclass
        return self

    def __next__(self):
        return next(self.rows)
