import os
import random
import sys

import pandas as pd

import BioTK.mmat
from . import connect, fetch_table

MATRIX_BASE = "/home/gilesc/data/ncbi/geo/matrix/taxon/"
MATRIX_BASE = "/home/gilesc/control/GPL570/"
MATRICES = {}

def get_matrix(taxon_id,
               tissue=None,
               raw=False,
               index="sample"):
    key = (taxon_id, index, "raw" if raw else "normalized")
    if key not in MATRICES:
        path = os.path.join(MATRIX_BASE,
                            "%s/%s/%s" % key)
        MATRICES[key] = BioTK.mmat.MMAT(path)
    m = MATRICES[key]
    return m

def control_for(X, groups):
    # index = sample
    # column = gene
    return X.mean() + X.groupby(groups).transform(lambda g: g - g.mean())

import sklearn.linear_model

def impute(X):
    """
    Impute missing values for each column.
    Drops columns with all NaN.
    """
    X = X.dropna(axis=1, how="all")
    for i in range(X.shape[1]):
        x = X.iloc[:,i]
        x[x.isnull()] = x.mean()
    return X

def infer_binary_label(X, labels):
    """
    Using labels (pandas Series) as a training set,
    train a classifier and infer the most likely
    label for the unlabeled rows in X.
    """
    labels = labels[labels.index.isin(X.index)]\
        .dropna()
    if labels.index.isin(X.index).all():
        return labels

    ix = labels.index
    labels = pd.Categorical.from_array(labels)
    labels.index = ix

    X = impute(X)

    model = sklearn.linear_model.LogisticRegression()
    X_tr = X.loc[labels.index,:]
    X_te = X.ix[~X.index.isin(X_tr.index),:]
    model.fit(X_tr, labels.labels)
    y_te = model.predict(X_te)
    y_te = labels.levels[y_te]
    y_te.index = X_te.index

    o = list(labels.levels[labels.labels]) + list(y_te)
    o = pd.Series(o, index=list(labels.index) + list(y_te.index))
    return o

def tissue_mean(taxon_id, tissue):
    pass

def mean_per_tissue(taxon_id):
    m = get_matrix(taxon_id, raw=True)
    attr = fetch_table("channel_attribute")
    attr = attr.ix[attr["taxon_accession"] == \
                   taxon_id,:]
        #.drop_duplicates(subset=["channel_accession"])
    attr.index = attr["channel_accession"]
    tissues = attr["tissue_accession"]
    data = {}

    ###TEMP HACK
    tissues_sel = set(["BTO:0000759", "BTO:0000763", "BTO:0001103",
                       "BTO:0001253", "BTO:0001379", "BTO:0002900"]) \
        & set(tissues)

    #for tissue in sorted(set(tissues)):
    for tissue in tissues_sel:
        ###END
        ix = tissues == tissue
        accessions = list(set(m.index) & \
            set(attr.ix[ix,:]["channel_accession"]))
        print(accessions, file=sys.stderr)
        if not accessions or len(accessions) < 25:
            continue
        print(tissue, len(accessions), file=sys.stderr)
        random.shuffle(accessions)
        #accessions = accessions[:500]

        X = m.loc[accessions,:].to_frame()
        if False:
            X = control_for(X, attr["series_accession"])
            gender = attr["gender"][accessions]
            if len(set(gender.dropna())) == 2:
                if gender.isnull().any():
                    gender = infer_binary_label(X, gender)
                X = control_for(X, attr["gender"])

        data[tissue] = X.mean()

        #if len(data) == 2:
        #    break

    o = pd.DataFrame.from_dict(data)
    o.index.name = "Gene ID"
    return o

if __name__ == "__main__":
    mean_per_tissue("9606")\
        .to_csv(sys.stdout, sep="\t")
