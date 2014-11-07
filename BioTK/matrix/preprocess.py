from itertools import islice

import pandas as pd
import numpy as np

"""
class MatrixOp(object):
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def apply(handle, parallel=True):
        pass
"""

def log_transform(x, shift=True, range=-1, base=2):
    factor = 1 / np.log(base)
    if shift:
        x -= x.min() - 1
    if x.max() - x.min() > range:
        return x.apply(np.log) * factor
    return x

def standardize(x):
    return (x - x.mean()) / x.std()

if __name__ == "__main__":
    import sys
    from BioTK.matrix import read
    read(sys.stdin).apply(log_transform).dump()
