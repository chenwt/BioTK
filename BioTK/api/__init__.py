import functools
import os
import socket

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, t as t_dist
from celery import Celery, group
from celery.signals import worker_process_init

from BioTK.db import *
from BioTK.io.BBI import BigWigFile
from centrum.mmat import MMAT

# The minimum samples required for a meaningful analysis
MIN_SAMPLES = 25
MAX_SAMPLES = 100 if socket.gethostname() == "phoenix" else 400
store = data = region_db = None
db = get_session()

API = Celery("BioTK")
API.config_from_object("celeryconfig")

def correlate(x, y):
    ix = ~(np.isnan(x) | np.isnan(y))
    return pearsonr(x[ix], y[ix])

@functools.lru_cache()
def gene_info():
    return pd.DataFrame.from_records(
        [(g.id, g.symbol, g.name) for g in db.query(Gene)],
        columns=["Gene ID", "Symbol", "Name"])\
                .set_index("Gene ID")

class TaxonDataset(object):
    def __init__(self, taxon_id):
        self.taxon_id = taxon_id
        self.X = MMAT("/data/public/expression/%s.mmat" % taxon_id)
        attribute_path = "/data/public/attributes/%s.attrs" % \
                taxon_id
        self.A = pd.read_csv(attribute_path,
                index_col=0, sep="\t", header=0)\
                        .dropna(subset=["Age", "Tissue"])
        # Drop all detected disease samples and samples w/o expression
        self.A = self.A.ix[self.A["Disease"].isnull(),:]\
                .drop("Disease", axis=1)
        self.A = self.A.ix[list(set(self.X.index) & set(self.A.index)),:]
        # Also, to remove outliers and incorrectly detected ages,
        # only use ages in the middle 90% of age distribution
        if taxon_id == 9606:
            age_lb = 25 * 12
            age_ub = 70 * 12
        else:
            age_lb = self.A["Age"].quantile(0.05)
            age_ub = self.A["Age"].quantile(0.95)
        ix = (self.A["Age"] >= age_lb) & (self.A["Age"] <= age_ub)
        self.A = self.A.ix[ix,:]

    def expression(self, samples):
        index = list(set(samples) & set(self.X.index))
        return self.X.loc[index, :].to_frame()

    def tissue_age_correlation(self, tissue):
        A = self.A.loc[self.A["Tissue"] == tissue, :]
        X = self.expression(A.index)
        A, X = A.align(X, join="inner", axis=0)
        X = X.ix[:,(~X.isnull()).sum(axis=0) > 25]

        o = X.mean(axis=0).to_frame("Mean Expression")
        n = o["N"] = (~X.isnull()).sum(axis=0)
        r, p = zip(*map(lambda i: correlate(X.iloc[:,i], A["Age"]), 
                range(X.shape[1])))
        p = np.maximum(1e-10, p)
        p = - np.log10(p)
        o["Age Correlation"] = r
        o["-log10(p)"] = p
        o.index = list(map(int, o.index))
        o = gene_info()\
                .join(o, how="inner")\
                .dropna()\
                .sort("Age Correlation", ascending=False)
        return o, X.shape[0]

    def gene_set_age_analysis(self, genes):
        A = self.A.ix[self.A["Tissue"].isin(tissues),:]\
                .groupby("Tissue")\
                .apply(lambda df: df.head(MAX_SAMPLES) \
                if df.shape[0] > MIN_SAMPLES else None)\
                .reset_index(level=0, drop=True)
        # Mean Z-score for the gene set
        x = self.expression(A.index)\
                .loc[:,genes]\
                .mean(axis=1)
        # Remove major outliers
        x = x[(x > -7) & (x < 7)]
        A["Expression"] = x
        A = A.dropna()
        o["expression"] = A.sort("Tissue")

        o["tissue"] = A.groupby("Tissue")\
                .apply(lambda df: pearsonr(df["Expression"], df["Age"])[0])\
                .to_frame("Age Correlation")
        o["tissue"]["Count"] = A.groupby("Tissue")\
                .apply(lambda df: df.shape[0])
        o["tissue"]["Mean Expression"] = \
                A.groupby("Tissue")["Expression"].mean()
        o["tissue"] = o["tissue"].sort("Age Correlation")
        return o

#############
# Global data
#############

@worker_process_init.connect
def initialize(sender, **kwargs):
    global data
    data = dict((taxon_id, TaxonDataset(taxon_id))
            for taxon_id in [9606, 10116, 10090])

#######
# Tasks
#######

@API.task
def gene_set_age_analysis_single_tissue(taxon_id, genes, tissue):
    dset = data[taxon_id]
    genes = list(set(genes) & set(dset.X.columns))
    if not genes:
        return
    A = dset.A.ix[dset.A["Tissue"] == tissue,:].head(MAX_SAMPLES)
    x = dset.expression(A.index).loc[:,genes].mean(axis=1)
    if len(x) < MIN_SAMPLES:
        return
    A["Expression"] = x
    A = A.dropna()
    r, p = pearsonr(A["Expression"], A["Age"])
    summary = pd.Series([
        r, p,
        A.shape[0],
        A["Expression"].mean()],
        index=["Age Correlation", "Age Correlation P-Value", 
            "Count", "Mean Expression"])
    expression = A
    return tissue, summary, expression

@functools.lru_cache()
def gene_set_age_analysis(taxon_id, genes):
    tissues = tissue_counts.delay(taxon_id).get().index[:10]
    r = group(gene_set_age_analysis_single_tissue.s(taxon_id, 
        genes, t)
        for t in tissues)()
    try:
        tissues, summaries, expressions = \
                zip(*(x for x in r.get() if x is not None))
    except ValueError:
        # No results in any tissue
        return
    expression = pd.concat(expressions)
    summary = pd.concat(summaries, axis=1).T
    summary.index = tissues
    return {"expression": expression,
            "tissue": summary}

@API.task
def tissue_counts(taxon_id):
    return data[taxon_id]\
            .A["Tissue"]\
            .value_counts()\
            .order(ascending=False)

@API.task
def tissue_age_correlation(taxon_id, tissue):
    return data[taxon_id].tissue_age_correlation(tissue)

@API.task
def statistics():
    expression_counts = []
    for taxon_id, dataset in data.items():
        name = db.query(Taxon).get(taxon_id).name
        X = dataset.X
        A = dataset.A
        count = X.shape[0]
        labelled_count = len(set(X.index) &
                set(A.dropna(subset=["Age", "Tissue"]).index))
        expression_counts.append((taxon_id, name, count, labelled_count))

    return pd.DataFrame.from_records(expression_counts,
        columns=["Taxon ID", "Species", "Expression", 
            "Expression + Age/Tissue Label"])\
                    .sort("Expression", ascending=False)

@API.task
def taxon_statistics(taxon_id):
    taxon_id = int(taxon_id)
    df = data[taxon_id]\
            .A["Tissue"]\
            .value_counts()\
            .order(ascending=False)\
            .head(15)\
            .to_frame("Count")
    df["Tissue"] = df.index
    return df.ix[:,["Tissue", "Count"]]

# Sub-modules

from . import region
