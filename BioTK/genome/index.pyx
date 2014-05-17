"""
Various types of indices for genomic regions, both RAM and disk-based.
"""

from itertools import groupby
from operator import attrgetter


from sortedcontainers import SortedList

__all__ = ["RAMIndex", "GenomicRegionRAMIndex"]

cdef class Node:
    def __init__(self, list intervals):
        if len(intervals) == 0:
            return

        midpoint = int(len(intervals) / 2)
        self.payload = intervals[midpoint]
        self.max_end = self.payload.end
        if midpoint > 0:
            self.left = Node(intervals[:midpoint])
            self.max_end = max(self.max_end, self.left.max_end)
        if midpoint < len(intervals) - 1:
            self.right = Node(intervals[(midpoint+1):])
            self.max_end = max(self.max_end, self.right.max_end)

    def search(self, list result, long start, long end):
        if start > self.max_end:
            return
        if self.left:
            self.left.search(result, start, end)
        if (start < self.payload.end) and (end > self.payload.start):
            result.append(self.payload)
        if end < self.payload.start:
            return
        if self.right:
            self.right.search(result, start, end)

cdef class RAMIndex:
    """
    A RAM-based index for generic intervals.
    
    This is a simple augmented binary search tree as described
    in CLRS 2001.
    """
    def __init__(self):
        self._intervals = SortedList()
        self._built = False

    def add(self, Interval r):
        """
        Add another interval to the index. This method can only be
        called if the index has not been built yet.
        """
        assert(not self._built, 
                "Can't currently mutate a constructed RAMIndex.")
        self._intervals.add(r)

    def build(self):
        """
        Build the index. After this method is called, new intervals
        cannot be added.
        """
        self._root = Node(list(self._intervals))
        self._built = True

    def search(self, long start, long end):
        assert(self._built, "Must call %s.build() before using search()" % \
                self.__class__.__name__)
        assert(start < end, "start must be less than end")
        result = []
        self._root.search(result, start, end)
        return result

    def __iter__(self):
        return iter(self._intervals)

    def __len__(self):
        return len(self._intervals)

empty_index = RAMIndex()
empty_index.build()

cdef class GenomicRegionRAMIndex(object):
    """
    A RAM-based index for genomic regions on multiple chromosomes/contigs.
    """
    def __init__(self):
        self._indices = {}
        self._built = False

    def add(self, GenomicRegion r):
        assert(not self._built, 
                "Can't currently mutate a constructed RAMIndex.")
        if not r.contig in self._indices:
            self._indices[r.contig] = RAMIndex()
        self._indices[r.contig].add(r)

    def __len__(self):
        return sum(map(len, self._indices.values()))

    def build(self):
        for ix in self._indices.values():
            ix.build()
        self._built = True

    def __getitem__(self, str contig):
        return self._indices.get(contig, empty_index)

    def search(self, GenomicRegion q):
        """
        Search the index for intervals overlapping the given GenomicRegion.
        """
        start, end = sorted([q.start, q.end])
        try:
            ix = self._indices[q.contig]
        except KeyError:
            raise KeyError("No index found for contig: %s" % q.contig)

        return ix.search(start, end)
