import io
import os
import sys

import pandas as pd
import numpy as np

import BioTK.io
from BioTK.db import *

def extract(args):
    #genes, annotation, sample_id, data = args
    sample_id, data = args
    data = data.decode("utf-8")
    try:
        # FIXME: read which column the value is in from the 
        # included XML file (they aren't always in the same order)
        index, values = [], []
        lines = iter(data.strip().split("\n"))
        next(lines)
        for line in lines: 
            fields = line.split("\t")
            try:
                values.append(float(fields[1]))
                index.append(fields[0])
            except:
                continue
        if len(values) == 0:
            return
        expression = pd.Series(values, index=index).to_frame("Value").dropna()
        ix = annotation[expression.index]
        mu = expression.groupby(ix).mean().iloc[:,0]
        mu = mu + 1e-5 - mu.min()
        if mu.max() > 100:
            mu = mu.apply(np.log2)
        mu = (mu - mu.mean()) / mu.std()
        data = np.array(mu[genes])
        return sample_id, data
    except Exception as e:
        print(e, file=sys.stderr)
        #print(expression.dtypes, file=sys.stderr)
        #print(expression.head(), file=sys.stderr)
        pass

def extract_expression(miniml_archive):
    global genes, annotation
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
    annotation_path = "/data/public/geo/annotation/AILUN/GPL%s.annot.gz" % platform_id
    annotation = pd.read_table(annotation_path, 
            compression="gzip",
            usecols=[0,1],
            names=["Probe ID", "Gene ID"])
    probe_counts = annotation["Probe ID"].value_counts()
    unique_probes = probe_counts.index[probe_counts == 1]
    annotation.index = annotation["Probe ID"]
    annotation = annotation.ix[unique_probes, "Gene ID"]

    #mp.set_start_method("fork")
    p = mp.Pool()

    print("Sample ID", *genes, sep="\t")
    with tarfile.open(path, "r:xz") as archive:
        def items():
            for item in archive:
                if not (item.name.startswith("GSM") and \
                        item.name.endswith("-tbl-1.txt")):
                    continue
                sample_id = int(item.name.split("-")[0].lstrip("GSM"))
                data = archive.extractfile(item).read()
                yield sample_id, data
       
        total = 0
        for result in p.imap_unordered(extract, items(), chunksize=10):
            if result is not None:
                sample_id, data = result
                total += 1
                print(sample_id, *data, sep="\t")
                if total % 100 == 0:
                    print(total, file=sys.stderr)


"""
Using the GEOmetadb SQLite database, extract interesting attributes (age, tissue, gender, etc.)
from GEO sample descriptions.
"""

# TODO:
# - Associate a probability with each text-based and expression-inferred
#   label extraction
# - If a unit can't be found initially, instead of using a user-provided
#   default, store the ID, compute the empirical distribution of age 
#   (for this organism) then determine the maximum likelihood age for
#   unlabeled samples (e.g., if a human has 'age: 543', which sadly
#   happens, it's probably in months)
# - Detect controls among disease samples

from BioTK.db.geo import db, Sample

def attribute(species_name=None, default_age_unit=None):
    """
    p.add_argument("--default-age-unit", "-u", 
            choices=["year", "month", "hour" "day"])
    p.add_argument("--no-age-range", "-r",
            action="store_true",
            help="By default, samples labeled with age 'X to Y <units>' are labeled with the mean of X and Y.\
Specifying this argument throws out these samples.")
    """
    #use_age_range = not args.no_age_range
    assert default_age_unit in ["year", "month", "hour", "day", None]

    print("Sample ID", "Age", "Tissue", "Disease", sep="\t")
    for sample in db.query(Sample).filter_by(organism_ch1=species_name):
        age = sample.age(default_unit=default_age_unit)
        if age:
            row = [x or "" for x in \
                    [sample.id, age, sample.tissue, sample.disease]] 
            print(*row, sep="\t")
