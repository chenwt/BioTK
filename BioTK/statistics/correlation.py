import os
import multiprocessing as mp

import numpy as np
import pandas as pd
from scipy import stats, linalg
 
def _pcor(args):
    X,v,p,j = args
    ix = np.ones(p, dtype=bool)
    ix[j] = 0
    beta_j = linalg.lstsq(X[:,ix], X[:,j])[0]
    beta_v = linalg.lstsq(X[:,ix], v)[0]

    res_j = X[:,j] - X[:,ix].dot(beta_j)
    res_v = v - X[:,ix].dot(beta_v)
    
    return stats.pearsonr(res_v, res_j)[0]

def partial_correlation(X, v):
    """
    Returns the sample linear partial correlation coefficients between each
    column in the matrix X and the vector v, controlling for the remaining
    variables in X.

    Parameters
    ----------
    X : array-like, shape (n, p)
        Array with the different variables. 
        Each column of C is taken as a variable

    v : array-like, shape (n)
        The vector to compute partial correlations with.

    Returns
    -------
    P : array-like, shape (p, p)
        P[j] contains the partial correlation of C[:, j] and v,
        controlling for the remaining variables in C.

    (adapted from: https://gist.github.com/fabianp/9396204419c7b638d38f)
    """
    if isinstance(X, pd.DataFrame):
        X = X.dropna(axis=1, how="any")
        if isinstance(v, pd.Series):
            X, v = X.align(v.dropna(), axis=0, join="inner")
        columns = X.columns
    assert X.shape[0] == len(v)

    X = np.asarray(X)
    v = np.asarray(v)
    p = X.shape[1]
    pool = mp.Pool(os.cpu_count() - 2)
    partial = pool.map(_pcor, ((X,v,p,j) for j in range(p)))
    partial = np.array(partial)

    if columns is not None:
        partial = pd.Series(partial, index=columns)

    return partial
