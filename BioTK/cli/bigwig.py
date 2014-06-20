import os
import operator
import itertools
import multiprocessing as mp
import sys

import numpy as np
from click import argument, option

from BioTK.cli.core import btk
from BioTK.io import BEDFile
from BioTK.io.BBI import BigWigFile
from BioTK.genome import Contig

@btk.group()
def bigwig():
    """
    Manipulate BigWig files
    """

def _read_regions(path):
    with BEDFile(path) as h:
        regions = [rg for rg in h if rg.name and len(rg) > 0]
    regions.sort(key=operator.attrgetter("name"))
    return regions

def _query(args):
    path, region_file, normalize, log_transform = args
    regions = _read_regions(region_file)
    try:
        bw = BigWigFile(path)
        values = bw.mean(regions)
    except Exception as e:
        print(e, file=sys.stderr)
        return
    if normalize:
        min_value = max(1e-10, np.min(values[values > 0]))
        values[values == 0] = min_value
        if log_transform:
            values = values.apply(np.log2)
        values = (values - values.mean()) / values.std()
    sample_name = os.path.splitext(os.path.basename(path))[0]
    return sample_name, values

@bigwig.command()
@option("--region-file", "-r", required=True)
@option("--normalize", "-n", default=False, is_flag=True)
@option("--log-transform", "-l", default=False, is_flag=True)
@argument("bigwig_files", required=True, nargs=-1)
def query(bigwig_files, 
        region_file=None, normalize=False, log_transform=False):
    """
    Extract a matrix of (possibly normalized) counts from loci 
    (BED format) and BigWig files.
    """
    regions = _read_regions(region_file)
    keys = list(sorted(set(r.name for r in regions)))
    print("Key", *keys, sep="\t")

    p = mp.Pool()
    for rs in p.imap_unordered(_query, 
            ((path, region_file, normalize, log_transform)
        for path in bigwig_files)):
        if rs is not None:
            sample_name, values = rs
            print(sample_name, *values, sep="\t")
