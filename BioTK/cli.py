from click import group, command, argument

@group()
def btk():
    pass

@btk.group()
def db():
    """
    Query or modify the BioTK database
    """
    pass

@btk.group()
def geo():
    """
    Manipulate data from NCBI GEO
    """
    pass

import os
import sys
from BioTK.db import *
import BioTK.io
import pandas as pd
import numpy as np

@geo.command("extract-expression")
@argument("miniml_archive")
def geo_extract_expression(miniml_archive):
    path = miniml_archive

    session = get_session()
    platform_id = int(os.path.basename(path).split(".")[0][3:])
    genes = np.array([g.id for g in \
            session.query(Gene)\
                .join(Taxon)\
                .join(GEOPlatform)\
                .filter(GEOPlatform.id==platform_id)\
                .order_by(Gene.id).all()])
    #url = "ftp://ailun.stanford.edu/ailun/annotation/geo/GPL%s.annot.gz" \
    #        % platform_id
    #annotation_path = BioTK.io.download(url)
    annotation_path = "/data/geo/annotation/AILUN/GPL%s.annot.gz" % platform_id
    annotation = pd.read_table(annotation_path, 
            compression="gzip",
            usecols=[0,1],
            names=["Probe ID", "Gene ID"])
    probe_counts = annotation["Probe ID"].value_counts()
    unique_probes = probe_counts.index[probe_counts == 1]
    annotation.index = annotation["Probe ID"]
    annotation = annotation.ix[unique_probes, "Gene ID"]

    print("Sample ID", *genes, sep="\t")
    with tarfile.open(path, "r:xz") as archive:
        for chunk in BioTK.util.chunks(archive, 1000):
            for item in chunk:
                if not (item.name.startswith("GSM") and \
                        item.name.endswith("-tbl-1.txt")):
                    continue
                try:
                    sample_id = int(item.name.split("-")[0].lstrip("GSM"))

                    handle = archive.extractfile(item)
                    # FIXME: read which column the value is in from the 
                    # included XML file (they aren't always in the same order)
                    expression = pd.read_table(handle, 
                            header=None, 
                            index_col=0,
                            names=["Probe ID", "Value"],
                            dtype={
                                "Probe ID": object,
                                "Value": np.float64},
                            usecols=[0,1])
                    ix = annotation[expression.index].dropna()
                    mu = expression.groupby(ix).mean().iloc[:,0]
                    mu = mu + 1e-5 - mu.min()
                    if mu.max() > 100:
                        mu = mu.apply(np.log2)
                    mu = (mu - mu.mean()) / mu.std()
                    data = np.array(mu[genes])
                    print(sample_id, *data, sep="\t")
                except Exception as e:
                    print(e, file=sys.stderr)
                    print(expression.dtypes, file=sys.stderr)
                    print(expression.head(), file=sys.stderr)
