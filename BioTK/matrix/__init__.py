import itertools
import sys

import numpy as np
import pandas as pd

class MatrixIterator(object):
    N_JOBS = 8

    def __init__(self, rows, columns=None, header=True):
        self.rows = iter(rows)
        self.header = header
        self.columns = columns

    def __iter__(self):
        # Override in subclass
        return self.rows

    def dump(self, handle=sys.stdout, delimiter="\t", precision=3):
        rows = iter(self)
        if self.header:
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
                yield fn(row, **kwargs)
        return MatrixIterator(generator(), header=self.header)
