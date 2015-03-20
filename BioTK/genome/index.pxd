# cython: language = c++

from cpython cimport bool

from BioTK.genome.types cimport Interval, GenomicRegion

cdef:
    class Node:
        cdef:
            Interval payload
            Node left, right
            long max_end

    class RAMIndex:
        cdef readonly:
            object _intervals
            object _root
            bool _built

    class GenomicRegionRAMIndex:
        cdef:
            object _indices
            bool _built
