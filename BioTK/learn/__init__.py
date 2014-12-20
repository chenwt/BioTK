from .hyperparameter import *
from .cv import *

import numpy as np
from pandas import DataFrame, SparseSeries, Series

from BioTK.io import gopen
from BioTK import mixin

from collections import namedtuple
PerformanceB = namedtuple("PerformanceB", ["N", "AUC"])

class Problem(mixin.Pickleable):
    """
    A class encapsulating a training set, and possibly unlabeled samples,
    with associated predictors.
    """

    def __init__(self, X: DataFrame, y):
        if isinstance(y, SparseSeries):
            y = y.to_dense()
        assert isinstance(y, Series)
        assert X.ndim == 2
        assert y.ndim == 1
        self._X_tr, self._y_tr = X.align(y, axis=0, join="inner")
        self._X_te = X.ix[~X.index.isin(y.index),:]

        self.name = y.name
        self.n_predictors = X.shape[1]
        self.n_samples = X.shape[0]

    @staticmethod
    def random(n_samples=10, n_predictors=5, p=0.2):
        assert n_samples > n_predictors
        X = DataFrame(np.random.random((n_samples, n_predictors)))

        Y = max(int(n_samples * p), 1) * [1]
        Y.extend([0 for _ in range(n_samples - len(Y))])
        np.random.shuffle(Y)
        Y = Series(Y)
        return Problem(X, Y)

from sklearn import metrics

def predict_validate(model, problem, predict_all=False):
    """
    predict_all : If True, use the predictor to predict values
        for *all* samples, even those that are part of the training set.
        If False, use the known values for training samples and
        predicted values for non-training samples.
    """
    X = problem._X_tr.as_matrix()
    y = problem._y_tr.as_matrix()
    y_hat = cross_validate(model, X, y)
    perf = PerformanceB(len(y), metrics.roc_auc_score(y, y_hat))
    if not predict_all:
        y_hat = problem._y_tr
    else:
        y_hat = pd.Series(y_hat, index=problem._y_tr.index)

    if problem._X_te.shape[0] > 0:
        X_te = problem._X_te.as_matrix()
        model.fit(X,y)
        y_hat.append(pd.Series(model.predict_log_proba(X_te), 
            index=X_te.index))

    return y_hat, perf
