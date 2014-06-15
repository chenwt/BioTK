import subprocess as sp
import os
import glob

import numpy as np
import pandas as pd

from celery import group
from celery.signals import worker_process_init

from BioTK.io.BBI import BigWigFile
from BioTK.api import API, gene_info

@API.task
def region_expression_single_locus(path, contig, start, end):
    id = os.path.splitext(os.path.basename(path))[0]
    try:
        mu = sp.check_output(["/usr/local/bin/bigWigSummary", "-type=mean", path, contig, str(start), str(end), str(1)]).decode("utf-8")
        mu = float(mu)
    except Exception as e:
        mu = np.nan
    return id, mu

from centrum import MMAT

def region_expression(taxon_id, genome_build, contig, start, end):
    dir = "/data/lab/seq/rna/9606/hg19/"
    paths = glob.glob(dir + "*.bw")
    taxon_id = int(taxon_id)
    s = dict(group(region_expression_single_locus.s(path, contig, start, end)
        for path in paths)().get())
    s = pd.Series(s)
    X = MMAT("/data/lab/seq/rna/9606/hg19/eg.mmat")
    s = s[X.columns]
    o = X.correlate(s).to_frame("Correlation")
    o.index.name = "Gene ID"
    return gene_info()\
            .join(o, how="inner")\
            .dropna()\
            .sort("Correlation", ascending=False)
