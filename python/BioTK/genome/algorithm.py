def _intersect_sorted(rs1, rs2):
    """
    Implements the 'chromSweep' algorithm, as introduced here:

    - https://github.com/arq5x/chrom_sweep

    Parameters
    ----------
    rs1 : iterable of BioTK.genome.Region objects
    rs2 : iterable of BioTK.genome.Region objects

    Requires that both rs1 and rs2 be sorted by contig, then by start
    coordinate.
    """
    pass

def intersect(rs1, rs2, assume_sorted=False):
    """
    Parameters
    ----------
    rs1 : iterable of BioTK.genome.Region objects
    rs2 : iterable of BioTK.genome.Region objects
    """
    # TODO: Should probably construct an IntervalTree/RAMIndex in this case
    assert(assume_sorted, "Intersection for non-sorted region sets not implemented.")
