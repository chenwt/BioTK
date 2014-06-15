import os
import operator
import itertools

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

@bigwig.command()
@option("--region-file", "-r", required=True)
@option("--normalize", "-n", default=False, is_flag=True)
@argument("bigwig_files", required=True, nargs=-1)
def query(bigwig_files, region_file=None, normalize=False):
    """
    Do some stuff
    """
    with BEDFile(region_file) as h:
        regions = [rg for rg in h if rg.name and len(rg) > 0]
    regions.sort(key=operator.attrgetter("name"))

    keys = list(sorted(set(r.name for r in regions)))
    print("Key", *keys, sep="\t")
    for path in bigwig_files:
        try:
            bw = BigWigFile(path)
        except:
            continue
        values = []
        for key, rgs in itertools.groupby(regions, lambda rg: rg.name):
            size = sum = 0
            for rg in rgs:
                s = bw.summarize_region(rg.contig.name, rg.start, rg.end)
                size += s.size
                sum += s.sum
            mu = sum / size
            values.append(mu)
        values = np.array(values)
        if normalize:
            min_value = np.min(values[values > 0])
            values[values == 0] = min_value
            values = np.log2(values)
            values -= values.mean()
        sample_name = os.path.splitext(os.path.basename(path))[0]
        print(sample_name, *values, sep="\t")
