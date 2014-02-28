"""
Various types of indices for genomic intervals, both RAM and disk-based.
"""

__all__ = ["RAMIndex"]

class IntervalNode(object):
    __slots__ = ["_start", "_end", "_data", 
            "_left", "_right", "_max_end"]

    def __init__(self, intervals):
        midpoint = int(len(intervals) / 2)
        start, end, data = intervals[midpoint]
        self._start = start
        self._end = end
        self._data = data
        self._left = None
        self._right = None
        self._max_end = self._end
        if midpoint > 0:
            self._left = IntervalNode(intervals[:midpoint])
            self._max_end = max(self._end, self._left._max_end)
        if midpoint < len(intervals) - 1:
            self._right = IntervalNode(intervals[midpoint+1:])
            self._max_end = max(self._end, self._right._max_end)

    def search(self, start, end):
        if start > self._max_end:
            return
        if self._left:
            yield from self._left.search(start, end)
        if (start < self._end) and (end > self._start):
            yield self._data
        if end < self._start:
            return
        if self._right:
            yield from self._right.search(start, end)
    
    def __iter__(self):
        if self._left:
            yield from self._left
        yield self._data
        if self._right:
            yield from self._right

class IntervalTree(object):
    """
    A RAM-based index for (generic) intervals.
    
    This is a simple augmented binary search tree as described
    in CLRS 2001.
    """
    def __init__(self, intervals):
        intervals.sort()
        self._root = IntervalNode(intervals)
        
    def search(self, start, end):
        return self._root.search(start, end)
        
    def __iter__(self):
        return iter(self._root)

class RAMIndex(object):
    """
    A RAM-based index for genomic regions on multiple chromosomes.
    
    Internally, it stores one IntervalTree per chromosome.
    """
    def __init__(self):
        self._intervals = {}
        self._roots = {}
        self._built = False

    def add(self, chrom, start, end, data=None):
        """
        Add another interval to the index. This method can only be
        called if the index has not been built yet.
        """
        if self._built:
            raise Exception("Can't currently mutate a constructed IntervalTree.")
        self._intervals.setdefault(chrom, [])
        self._intervals[chrom].append((start, end, data))
    
    def build(self):
        """
        Build the index. After this method is called, new intervals
        cannot be added.
        """
        assert(self._intervals)
        for chrom, intervals in self._intervals.items():
            self._roots[chrom] = IntervalTree(intervals)
        self._built = True
    
    def search(self, chrom, start, end):
        """
        Search the index for intervals overlapping the given 
        chrom, start, and end.
        """
        if not self._built:
            raise Exception("Must call %s.build() before using search()" % \
                            str(type(self)))
        return self._roots[chrom].search(start, end)
    
    def __iter__(self):
        assert(self._built)
        for chrom, node in self._roots.items():
            yield from node
