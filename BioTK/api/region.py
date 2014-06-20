import subprocess as sp
import os
import glob
import sys
import tempfile

import numpy as np
import pandas as pd

from celery import group
from celery.signals import worker_process_init

from centrum import MMAT
from BioTK.io.BBI import BigWigFile
from BioTK.io import BEDFile
from BioTK.api import API, gene_info

@API.task
def region_expression_single_locus(path, contig, start, end):
    udc = "/dev/shm/udc"
    os.makedirs(udc, exist_ok=True)

    id = os.path.splitext(os.path.basename(path))[0]
    with tempfile.NamedTemporaryFile(mode="w") as h:
        print(contig, start, end, "X", sep="\t", file=h)
        h.flush()
        try:
            o = sp.check_output(["bigWigAverageOverBed", 
                path, h.name, "stdout"]).decode("utf-8")
            mu = float(o.split("\t")[4])
        except Exception as e:
            mu = np.nan
    return id, mu

@API.task
def gene_locus(taxon_id, genome_build, gene_id):
    genome_base = "/data/public/genome/"
    path = "%(genome_base)s%(taxon_id)s/%(genome_build)s/eg.bed" % locals()
    with BEDFile(path) as h:
        for region in h:
            if str(region.name) == str(gene_id):
                return region.contig.name, region.start, region.end

def correlation_table(cors):
    cors = cors.to_frame("Correlation")
    cors.index.name = "Gene ID"
    return gene_info()\
            .join(cors, how="inner")\
            .dropna()\
            .sort("Correlation", ascending=False)

def region_expression_for_gene(taxon_id, genome_build, gene_id):
    X = MMAT("/data/lab/seq/rna/9606/hg19/eg.mmat")
    if gene_id in X.index:
        s = X.loc[gene_id,:]
        return correlation_table(X.correlate(s))
    else:
        contig, start, end = api.region.gene_locus\
                .delay(taxon_id, genome_build, gene_id).get()
        return region_expression(taxon_id, genome_build, contig, start, end)

def region_expression(taxon_id, genome_build, contig, start, end):
    dir = "/data/lab/seq/rna/9606/hg19/"
    paths = glob.glob(dir + "*.bw")
    taxon_id = int(taxon_id)
    s = dict(group(region_expression_single_locus.s(path, contig, start, end)
        for path in paths)().get())
    s = pd.Series(s)
    X = MMAT("/data/lab/seq/rna/9606/hg19/eg.mmat")
    s = s.loc[X.columns]
    return correlation_table(X.correlate(s))
    
