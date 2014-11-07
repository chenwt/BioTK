import itertools
import sys

import numpy as np
import pandas as pd

class MatrixIterator(object):
    N_JOBS = 8

    def __init__(self, rows):
        self.rows = iter(rows)

    def __iter__(self):
        # Override in subclass
        return self.rows

    def dump(self, handle=sys.stdout, delimiter="\t", precision=3):
        rows = iter(self)
        row = next(rows)
        print("", *row.index, sep=delimiter, file=handle)
        fmt = "{0:0." + str(precision) + "f}"
        for row in itertools.chain([row], rows):
            data = list(map(fmt.format, row))
            print(row.name, *data, sep=delimiter, file=handle)

    def apply(self, fn, **kwargs):
        def generator():
            for row in self:
                yield fn(row, **kwargs)
        return MatrixIterator(generator())
