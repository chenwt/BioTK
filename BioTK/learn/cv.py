"""
Utilities for cross-validation and performance metrics.
"""

__all__ = ["cross_validate"]

import multiprocessing as mp

import numpy as np
from sklearn.cross_validation import KFold

def _cross_validate(args):
    model, tr, te, X, y = args
    model.fit(X[tr,:], y[tr])
    return te, model.predict_log_proba(X[te,:])

def cross_validate(model, X, y, k=5, n_jobs=-1):
    """
    Run K-fold cross-validation in parallel on a supervised
    learning classifier, **returning the predictions**.

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

    Returns
    -------
    A tuple of (y, y_hat), where:
    y_hat : an array of predictions, the same shape as y
    """
    assert len(y.shape) == 1

    # Supposedly, on Linux, X and y won't be duplicated
    # http://stackoverflow.com/questions/10721915/shared-memory-objects-in-python-multiprocessing
    n_jobs = mp.cpu_count() if n_jobs==-1 else n_jobs
    kf = KFold(y.shape[0], k, shuffle=True)
    jobs = [(model, tr, te, X, y) for (tr,te) in kf]
    pool = mp.Pool(n_jobs)
    y_hat = np.zeros(y.shape)
    for te, y_hat_ in pool.imap(_cross_validate, jobs):
        y_hat[te] = y_hat_
    return y_hat
