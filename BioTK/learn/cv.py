"""
Utilities for cross-validation and performance metrics.
"""

import multiprocessing as mp

import numpy as np
import pandas as pd
from sklearn.cross_validation import StratifiedKFold, KFold

def _cross_validate(args):
    model, tr, te, X, y = args
    model.fit(X.iloc[tr,:], y.iloc[tr])
    try:
        y_hat = model.predict_log_proba(X.iloc[te,:])
        ix = list(model.classes_).index(1)
        y_hat = y_hat[:,ix]
    except AttributeError:
        y_hat = model.predict(X.iloc[te,:])
    return te, y_hat

def predictions(model, X, y, k=5, type="binary", n_jobs=-1):
    """
    Run K-fold cross-validation in parallel on a supervised
    learning classifier, **returning the predicted log-probabilities**.

    Parameters
    ----------
    model : sklearn supervised learning estimator object,
        implementing 'fit' and 'predict'
    X : array-like shape of at least 2D
    y : array-like, 1D
    k : int, optional
        The number of folds to use in cross-validation.
    n_jobs : int, optional
        The number of processors to use. If -1, use all processors.
        If 0, run serially.

    Returns
    -------
    A tuple of (y, y_hat), where:
    y_hat : an array of predictions, the same shape as y
    """
    assert len(y.shape) == 1
    assert isinstance(n_jobs, int)
    assert isinstance(k, int)
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert type in ("binary", "multilabel")
    
    #counts = y.value_counts()
    #counts.sort()
    #k = min(counts.iloc[0], k)
    #assert k > 1

    # Supposedly, on Linux, X and y won't be duplicated
    # http://stackoverflow.com/questions/10721915/shared-memory-objects-in-python-multiprocessing
    #kf = StratifiedKFold(y, k, shuffle=True)
    kf = KFold(len(y), n_folds=k, shuffle=True)
    jobs = [(model, tr, te, X, y) for (tr,te) in kf]
    y_hat = np.zeros(y.shape)
    if n_jobs != 0:
        n_jobs = mp.cpu_count() if n_jobs==-1 else n_jobs
        pool = mp.Pool(n_jobs)
        rs = pool.imap(_cross_validate, jobs)
    else:
        rs = map(_cross_validate, jobs)
    for te, y_hat_ in rs:
        y_hat[te] = y_hat_
    return pd.Series(y_hat, index=y.index)
