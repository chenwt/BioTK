import sys
from os.path import abspath, dirname, join
from collections import defaultdict

import pandas as pd

def identity(x):
    return x

class ResourceLookup(object):

    def __init__(self, pkgname):
        module = __import__(pkgname)
        self._basedir = abspath(join(dirname(module.__file__), 
            "..", "resources"))

    def path(self, relpath):
        """
        Get an absolute path to a data resource.
        """
        return join(self._basedir, relpath)

    def handle(self, relpath, mode="r"):
        """
        Get a file handle to a data resource.
        """
        return open(self.path(relpath), mode=mode)

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

class MultiMap(defaultdict):
    def __init__(self, *args, **kwargs):
        super(MultiMap, self).__init__(set, *args, **kwargs)

    def counts(self):
        o = {}
        for k,vs in self.items():
            o[k] = len(vs)
        return o

    def invert(self):
        """
        Invert the multimap, making keys values and values keys.
        """
        o = MultiMap()
        for k,vs in self.items():
            for v in vs:
                o[v].add(k)
        return o

    @property
    def T(self):
        return self.invert()

    def flatten(self, smallest=True, inverted=False):
        """
        For each value, if it has multiple keys, assign it
        to the key that has either the smallest or largest
        number of values (depending on the "smallest")
        parameter, and remove it from other keys.
        
        Returns a plain dict of (original) keys to values,
        if inverted is False, otherwise the inversion.
        """
        counts = self.counts()
        o = {}
        for v,ks in self.invert().items():
            k = sorted(ks,
                    key=counts.get, reverse=not smallest)[0]
            if inverted:
                k,v = v,k
            o[v] = k
        return o

    def to_frame(self, sparse=True):
        columns = list(sorted(self.invert().keys()))
        data = {}
        for k,vs in self.items():
            row = [1 if c in vs else 0 for c in columns]
            data[k] = pd.Series(row, dtype=int,
                    index=columns).to_sparse(fill_value=0)
        o = pd.SparseDataFrame.from_dict(data)
        if not sparse:
            o = o.to_dense()
        return o

def error(msg):
    """
    Exit with an error without showing huge backtraces.
    """
    sys.stderr.write(msg + "\n")
    sys.exit(1)

def error_if(test, msg=None):
    """
    Like (negated) assert, but without a backtrace.
    """
    if test:
        if msg is not None:
            error(msg)
        else:
            sys.exit(1)

def prt(*args, **kwargs):
    """
    Print *args, tab-delimited.
    **kwargs are passed to print()
    """
    args = list(args)
    for i,arg in enumerate(args):
        if isinstance(arg, float):
            args[i] = round(arg, 3)
    print(*args, sep="\t", **kwargs)


