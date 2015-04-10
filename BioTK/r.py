import enum
import sys
import os
from contextlib import redirect_stdout

import pandas as pd
import numpy as np
import patsy

R_INITOPTIONS = ("rpy2", "--vanilla")
import rpy2.rinterface 
rpy2.rinterface.initoptions = R_INITOPTIONS

from rpy2.robjects import r, StrVector, \
    ListVector, IntVector, FloatVector, DataFrame, Matrix
from rpy2.robjects.packages import importr as _importr
import rpy2.rlike.container as rlc

def importr(pkgname):
    with open(os.devnull, "w") as h:
        with redirect_stdout(h):
            pkg = _importr(pkgname)
    return pkg

#################################
# Coerce DataFrames to and from R
#################################

NP2R = {
        "float64": FloatVector,
        "int64": IntVector,
        "object": StrVector
}

def to_r(self, matrix=False):
    # TODO: rpy2 itself has a converter, see doc
    #import pandas.rpy.common as pdr

    columns = []
    for c,dt in zip(self.columns, self.dtypes):
        ctor = NP2R[dt.name]
        columns.append((c,ctor(self[c])))
    df = DataFrame(rlc.OrdDict(columns))
    df.rownames = list(map(str, self.index))
    if matrix:
        return r["as.matrix"](df)
    return df
    
def _strip_x(ix):
    x = ix[0]
    convert = isinstance(x,str) \
            and x.startswith("X") \
            and x[1:].isdigit()
    if convert:
        ix = [int(x[1:]) for x in ix]
    return ix

def from_r(df):
    if isinstance(df, Matrix):
        df = r["as.data.frame"](df)
    cs = r.colnames(df)
    data = {}
    for c,x in zip(cs,df):
        data[c] = np.array(x)
    o = pd.DataFrame.from_dict(data)
    o.index=_strip_x(list(r.rownames(df)))
    o = o.ix[:,map(str, cs)]
    o.columns = _strip_x(o.columns)
    return o

def replace_index_names(X, names_from, names_to, axis=1):
    assert len(names_from) == len(names_to)
    assert axis in (0,1)
    if axis == 0:
        X = X.T

    columns = list(X.columns)
    for nf,nt in zip(names_from, names_to):
        for i,c in enumerate(columns):
            if c == nf:
                columns[i] = nt
                break

    X.columns = columns
    if axis == 0:
        X = X.T
    return X

ListVector.get = lambda self, key: self[self.names.index(key)]

pd.DataFrame.to_r = to_r
pd.DataFrame.from_r = from_r

##########
# Wrappers
##########

def _index(items):
    return dict(map(reversed, enumerate(items)))

def _make_design(D, formula):
    return patsy.dmatrix(formula, data=D, 
            return_type="dataframe")\
                    .dropna(how="any")

def _align(X,D):
    # FIXME: figure out if limma supports NaNs and add option accordingly
    X = X.T\
            .dropna(how="all", axis=1)\
            .dropna(how="all", axis=0)
    D,X = D.align(X, axis=0, join="inner")
    X = X.T
    return X,D

def _get_list_item(rlist, key):
    ix = _index(rlist.names)
    return rlist[ix[key]]

def _maybe_ints(ix):
    try:
        return list(map(int, ix))
    except ValueError:
        return list(ix)

def roast(X, D, sel, contrast, formula=None):
    assert type(contrast) in (int, str)

    # FIXME: qnorm, weight
    D = _make_design(D,formula) if formula is not None else D
    X,D = _align(X,D)
    X = quantile_normalize(X)
    if isinstance(contrast, str):
        contrast = list(D.columns).index(contrast)

    pkg = importr("limma")
    Dr = D.to_r()
    fit = pkg.lmFit(X.to_r(matrix=True),Dr)
    sigma = _get_list_item(fit, "sigma")
    df = _get_list_item(fit, "df.residual")
    sv = pkg.squeezeVar(FloatVector(np.array(sigma)**2), df=df)
    vprior = _get_list_item(sv, "var.prior")

    index = []
    rows = []
    sel = sel[list(set(sel.index) & set(X.index))]
    weights = FloatVector(np.array(sel))
    o = pkg.roast(
            y=X.loc[sel.index,:].to_r(),
            design=Dr,
            gene_weights=weights,
            contrast=contrast+1,
            var_prior=vprior, 
            df_prior=vprior)[0]
    o = pd.DataFrame.from_r(o)
    o.columns = ["proportion", "lp"]
    o["lp"] = -1 * o["lp"].apply(np.log10)
    return o

def quantile_normalize(X):
    pkg = importr("limma")
    Xn = pkg.normalizeBetweenArrays(X.to_r(matrix=True))
    o = pd.DataFrame.from_r(r["as.data.frame"](Xn))
    o.index = _maybe_ints(o.index)
    o.columns = _maybe_ints(o.columns)
    return o

class ExpressionType(enum.Enum):
    microarray = 1
    rt_pcr = 2
    rna_seq = 3

def limma(X, D, 
        formula=None,
        coefficients=None, 
        normalize=False, 
        type=ExpressionType.microarray,
        weighted=False):
    """
    Run limma on an expression and design matrix.

    Parameters
    ----------
    X : :class:`pandas.DataFrame`
        Expression matrix (genes x samples)

    D : :class:`pandas.DataFrame`
        Design matrix (samples x covariates), or, if "formula"
        is defined, a data frame of covariates to be turned into
        a design matrix according to the formula.

    coefficients : list of str or None, optional
        Run the analysis on these coefficients, which will affect the returned
        p-values and coefficients (the p-value reflects the proposition that
        any of the supplied coefficients significantly differ). If None,
        then all columns of D will be used.

    normalize : bool, optional
        Quantile normalize the data before analysis.

    weighted : bool, optional
        Use limma's "arrayWeights" function to determine the quality of
        each array and weight it appropriately in the analysis.

    formula : str or None, optional
        An optional formula string for the RHS of a linear model to extract
        covariates from D. If this parameter is supplied, it affects how "D" is
        interpreted (see also the documentation for D).

    type : :class:`ExpressionType`
        Indicates the type of expression data given by "X". 
        Processing will slightly differ depending on the type.

    Returns
    -------
    :class:`pandas.DataFrame`
        A table containing the model coefficients, F and B statistics,
        and adjusted and non-adjusted p-values for each gene/transcript.
    """
    assert isinstance(type, ExpressionType)
    assert type != ExpressionType.rt_pcr
        
    # Note: limma's input for expression is (genes x samples)
    if coefficients is not None:
        for c in coefficients:
            assert c in D.columns
    D = _make_design(D,formula) if formula is not None else D

    ix = list(set(X.columns) & set(D.index))
    X,D = X.loc[:,ix], D.loc[ix,:]

    for pattern in D.drop_duplicates().to_records(index=False):
        ok = set(X.index)
        for _,g in D.groupby(list(D.columns)):
            ok &= set(X.loc[:,D.index].dropna(how="all").index)
        X = X.loc[sorted(list(ok)),:]
    
    assert all(np.array(X.shape) > 0)
    ix = list(set(X.columns) & set(D.index))
    X,D = X.loc[:,ix], D.loc[ix,:]

    if normalize:
        if not type == ExpressionType.rna_seq:
            X = quantile_normalize(X)
    
    pkg = importr("limma")

    Xr = X.to_r(matrix=True)
    weights = pkg.arrayWeights(Xr) if weighted else r("NULL")
    fit = pkg.eBayes(pkg.lmFit(Xr,D.to_r(),weights=weights))

    if coefficients is None:
        coefficients = list(map(str, D.columns[1:]))
    coefficients_original = coefficients

    coefficients = StrVector(list(map(
        lambda x: str(x).replace(":","."), coefficients)))

    table = pkg.topTable(fit, 
            number=X.shape[0], 
            adjust_method="BH",
            coef=coefficients)
    o = pd.DataFrame.from_r(table)
    o = replace_index_names(o,
            ["AveExpr", "P.Value","adj.P.Val"],
            ["mu", "lp","FDR"])
    o["lp"] = - o["lp"].apply(np.log10)
    columns = list(o.columns)
    columns[:len(coefficients_original)] = coefficients_original
    o.columns = columns
    o["N"] = X.shape[1]
    return o.ix[:,["N"] + list(o.columns[:-1])]

def edger(X, D, formula=None, coefficients=None, weighted=None):
    # weighted: ignored
    assert formula is not None

    return_model = False
    if coefficients is not None:
        assert len(coefficients) == 1
        coef = list(D.columns).index(coefficients[0])
    else:
        return_model = True

    D = _make_design(D,formula)
    ix = list(set(X.columns) & set(D.index))
    X,D = X.loc[:,ix].astype(int), D.loc[ix,:]

    X[X==0] = np.nan
    for pattern in D.drop_duplicates().to_records(index=False):
        ok = set(X.index)
        for _,g in D.groupby(list(D.columns)):
            ok &= set(X.loc[:,D.index].dropna(how="all").index)
        X = X.loc[sorted(list(ok)),:]
    X = X.fillna(0)
 
    importr("splines")
    pkg = importr("edgeR")

    # TODO: if I am returning a model, is using a "DGEList" going to mess that up?
    # Such a model should not have to know about contrasts.
    Dr = D.to_r()
    Xr = X.to_r()
    dgl = pkg.DGEList(counts=Xr, group=Dr[1])
    dgl = pkg.calcNormFactors(dgl)
    dispersion = pkg.estimateGLMCommonDisp(dgl, Dr)
    dispersion = pkg.estimateGLMTagwiseDisp(dispersion, Dr)
    dispersion = pkg.estimateGLMTrendedDisp(dispersion, Dr)
    fit = pkg.glmFit(dispersion, Dr)
    if return_model:
        o = pd.DataFrame.from_r(fit.get("coefficients"))
        o.columns = D.columns
        return o
    comparison = pkg.glmLRT(fit, coef=2)
    table = r["as.data.frame"](pkg.topTags(comparison, 
        n=X.shape[0]))
    o = pd.DataFrame.from_r(table)
    o = replace_index_names(o,
            ["logCPM"], ["CPM"])
    o["CPM"] = 2 ** o["CPM"]
    o["SLPV"] = o["PValue"].apply(np.log10) * np.sign(o["logFC"])
    return o
