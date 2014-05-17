# cython: language = c++

import sys

__all__ = ["Interval", "GenomicInterval", "GenomicRegion", 
           "Contig", "Genome"]

cdef inline bint richcmp_helper(int compare, int op):
    """Returns True/False for each compare operation given an op code.
    Compare should act similarly to Java's comparable interface"""
    if op == 2: # ==
        return compare == 0
    elif op == 3: # !=
        return compare != 0
    elif op == 0: # <
        return compare < 0
    elif op == 1: # <=
        return compare <= 0
    elif op == 4: # >
        return compare > 0
    elif op == 5: # >=
        return compare >= 0

cdef inline bint cmp(x, y):
    return (x > y) - (x < y)

cdef Strand parse_strand(str strand):
    if strand == "+":
        return STRAND_FWD
    elif strand == "-":
        return STRAND_REV
    else:
        return STRAND_UNKNOWN

cdef str strand_to_string(Strand strand):
    if strand == STRAND_FWD:
        return "+"
    elif strand == STRAND_REV:
        return "-"
    else:
        return "."

cdef class Interval:
    def __init__(self, long start, long end, object data=None):
        self.start = start
        self.end = end
        self.data = data

    cpdef long length(self) except *:
        return self.end - self.start

    def __len__(self):
        return self.length()

cdef class GenomicInterval(Interval):
    def __init__(self, 
            long start, long end, 
            double score=0,
            str strand=".", 
            object data=None):
        self.score = score
        self._strand = parse_strand(strand)
        super(GenomicInterval, self).__init__(start, end, data)

    property strand:
        def __get__(self):
            return strand_to_string(self._strand)

    def __richcmp__(self, GenomicInterval o, int op):
        if self.start != o.start:
            return richcmp_helper(cmp(self.end, o.end), op)
        else:
            return richcmp_helper(cmp(self.start, o.start), op)

cdef class Contig:
    def __init__(self, str name, long id=-1, long size=-1):
        self.id = id
        if self.id == -1:
            self.id = hash(name)
        self.name = name
        self.size = size

    def __richcmp__(self, Contig o, int op):
        return richcmp_helper(cmp(self.id, o.id), op)

    def __hash__(self):
        return hash(self.id)

cdef class Genome:
    def __cinit__(self):
        self.by_id = {}
        self.by_name = {}

    def __init__(self, name=None):
        self.name = name

    def add(self, Contig ctg):
        self.by_id[ctg.id] = ctg
        self.by_name[ctg.name] = ctg

cdef class GenomicRegion(GenomicInterval):
    def __init__(self, 
            Contig contig, long start, long end, 
            str name="",
            double score=0,
            str strand=".",
            object data=None):
        #self.contig = sys.intern(contig)
        self.contig = contig
        self.name = sys.intern(name)
        super(GenomicRegion, self).__init__(start, end, 
                score=score, strand=strand, data=data)

    def __repr__(self):
        return "<GenomicRegion %s:%s-%s (%s)>" % \
                (self.contig.name, self.start, self.end, self.strand)

    def __richcmp__(self, GenomicRegion o, int op):
        if self.contig != o.contig:
            return richcmp_helper(cmp(self.contig, o.contig), op)
        elif self.start != o.start:
            return richcmp_helper(cmp(self.start, o.start), op)
        else:
            return richcmp_helper(cmp(self.end, o.end), op)
