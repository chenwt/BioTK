# cython: language = c++

from libcpp.map cimport map
from libcpp.string cimport string

cdef:
    enum Strand:
        STRAND_UNKNOWN = 0
        STRAND_FWD = 1
        STRAND_REV = 2

    str strand_to_string(Strand strand)
    Strand parse_strand(str strand)

    class Interval:
        cdef public:
            long start
            long end
            object data

        cpdef long length(Interval self)

    class GenomicInterval(Interval):     
        cdef public:
            double score
        cdef:
            Strand _strand

    class Contig:
        cdef public:
            str name
            long id
            long size

    class Genome:
        cdef public:
            str name
            dict by_id
            dict by_name

    class GenomicRegion(GenomicInterval):
        cdef public: 
            Contig contig
            str name


