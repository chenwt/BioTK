"""
Statistical methods for meta-analysis.
"""

import numpy as np
from scipy.stats import norm

def z_test(p,w=None,precision = 1e-10):
    """
    Combine multiple p-values using the (possibly weighted) z-test.

    Parameters
    ----------

    p : :class:`numpy.array`
        1-D array of the p-values.
    w : :class:`numpy.array`
        1-D array of the sample weights, the same length as p.
        If not provided, all samples are weighted the same.
    precision : float, optional
        The minimum possible p-value for the input sequence. 0s and 1s
        will be replaced with (value), or (1 - value), respectively.

    References
    ----------

    Chen, Z. Is the weighted z-test the best method for combining 
        probabilities from independent tests? Journal of Evolutionary
        Biology. 2010.
    """
    p = np.array(p).astype(float)
    assert ((p >= 0) & (p <= 1)).all()
    p[p==0] = 1e-10
    p[p==1] = 1 - 1e-10

    if w is None:
        w = np.ones(len(p))
    else:
        w = np.array(w).astype(float)
    assert (w > 0).all()

    z = (w * np.apply_along_axis(norm.ppf, 0, p)).sum() / (w ** 2).sum() ** 0.5
    return norm.cdf(-np.abs(z))
