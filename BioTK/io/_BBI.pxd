from BioTK.genome.types cimport Genome, Contig, GenomicRegion
from BioTK.genome.index cimport GenomicRegionRAMIndex

cdef:
    class BBIFile:
        cdef readonly:
            # Contig ids, names, and sizes
            Genome _genome
            # Index mapping genomic regions to BBI offsets
            # (with lazy loading)
            GenomicRegionRAMIndex _index

            str _path
            object _handle
            object _map

        cdef:
            void load_genome(self)
            void load_index(self)
