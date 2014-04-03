import pandas as pd
import numpy as np
from sklearn.preprocessing import Imputer

__all__ = ["quantile_normalize", "normalize", "collapse", "impute"]

def normalize(X, method="total_intensity", reference=None):
    # A variety of methods here:
    # http://www.nature.com/ng/journal/v32/n4s/full/ng1032.html

    # TODO: accept a series/array/dataframe for methods that can use a reference
    assert reference is None

    if method == "total_intensity":
        assert X.max().max() < 100, "The total_intensity method requires log2 transformed data."
        return X.apply(lambda x: x - x.mean(), axis=0)

def quantile_normalize(X, mu=None):
    """
    Quantile normalize an expression matrix.

    Parameters
    ----------
    X : :class:`pandas.DataFrame`
        The expression matrix to normalize, where samples are 
        columns and probes/genes are rows.
    mu : 1D array-like, optional
        An existing gene expression distribution to normalize against.
        If not provided, will use the row-wise mean of X.
    """
    X_n = X.copy().as_matrix()
    if mu is None:
        mu = X_n.mean(axis=1)
    else:
        mu = np.ravel(mu)
        # TODO: interpolate when shape is not the same
        assert len(mu) == X.shape[0]

    mu.sort()
    for j in range(X.shape[1]):
        ix = np.array(X.iloc[:,j].argsort())
        X_n[ix,j] = mu
    return pd.DataFrame(X_n, index=X.index, 
            columns=X.columns)

def impute(X, axis=0, strategy="mean"):
    # Add KNN
    imputer = Imputer(axis=axis, strategy=strategy)
    return pd.DataFrame(imputer.fit_transform(X.as_matrix()),
            index=X.index, columns=X.columns)

def collapse(X, by, axis=0, method="mean"):
    """
    Collapse a matrix by various methods. See: [1].

    Parameters
    ----------
    X : :class:`pandas.DataFrame`
        The matrix to collapse.
    by : :class:`pandas.Series`
        The groupings to collapse by. The elements in the series index
        should correpond to the index or column names of X (depending
        on the axis parameter), and the elements themselves are the 
        groups to collapse on.
    axis : int, default 0
    method : {"mean", "max"}
        The method to collapse by. Default: "mean".

    References
    ----------
    ..  [1] Miller et al. "Strategies for aggregating gene expression data:
        The collapseRows R function." BMC Bioinformatics 2011, 12:322.
        http://www.biomedcentral.com/1471-2105/12/322
    """
    assert axis in (0,1)
    assert method in ("mean", "max", "max_mean")

    if method == "mean":
        fn = lambda x: x.mean()
    elif method == "max":
        fn = lambda x: x.max()
    elif method == "max_mean":
        # This is really slow, so not public yet
        # FIXME: make it faster
        def fn(x):
            if isinstance(x, pd.Series):
                return x
            else:
                return x.ix[x.mean().order().index[-1],:]

    if axis == 1:
        return collapse(X.T, by, axis=0, method=method).T
    return X.groupby(by).agg(fn).dropna(how="all")
