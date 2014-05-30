"""
Analysis of gene/transcript sets.

Includes, (or could include), methods such as (GO or other ontology)
enrichment analysis, GSEA, rotation gene set analysis, etc.
"""

import pandas as pd
import numpy as np
from scipy.stats import ttest_ind, fisher_exact

import BioTK.expression

def roast_lite(X, C, p_grp, n_perm=100):
    """
    Like limma roast, except computes p-value by permuting samples
    instead of rotation set analysis (more sensitive, TODO).

    X : :class:`pandas.DataFrame`
        Expression matrix - transcripts (rows) vs samples (columns)
    C : :class:`pandas.DataFrame`
        Coefficient matrix - transcripts (rows) vs terms (columns)
    """
    # FIXME: use a contrast vector instead of p_grp
    p_grp = p_grp.copy()
    X, C = X.align(C, axis=0, join="inner")
    Xm = X.as_matrix()

    n = C.apply(lambda x: np.abs(x).sum())

    def t_stat(p_grp):
        ix = p_grp.as_matrix()
        t = ttest_ind(Xm[:,ix], Xm[:,~ix], axis=1)[0]
        t = pd.Series(t, index=X.index)
        return (C.T * t).sum(axis=1) / n

    y_true = t_stat(p_grp)
    y_perm = []
    for i in range(n_perm):
        np.random.shuffle(p_grp)
        y_perm.append(t_stat(p_grp))
    y_perm = pd.DataFrame(y_perm)

    p_up = (y_true >= y_perm).mean()
    p_down = (y_true <= y_perm).mean()
    return pd.DataFrame({
        "n": (C != 0).sum(axis=0),
        "t": y_true,
        "p_Up" : p_up,
        "p_Down" : p_down,
    }).ix[:,["n","t","p_Up","p_Down"]].sort("t")

def simple(members, C, min_annotated=5):
    """
    Classic enrichment analysis based on Fisher's Exact Test.

    members: :class:`pandas.Series`
        A boolean Series, with 'interesting' transcripts marked as
        True, and others False.
    C : :class:`pandas.DataFrame`
        Coefficient matrix - transcripts (rows) vs terms (columns)
    """
    # TODO: use chi2 if all cells > 5, otherwise FET?
    C, sel = C.astype(bool).align(members, join="inner", axis=0)
    C = C.ix[:,C.sum() >= min_annotated]

    isect = C.apply(lambda c: (c & sel).sum())
    sel_non_isect = sel.sum() - isect
    non_sel_isect = C.apply(lambda c: (c & ~sel).sum())
    total = C.shape[0]
    non_sel_non_isect = total - (isect + sel_non_isect + non_sel_isect)
    input = list(zip(zip(isect, sel_non_isect), 
        zip(non_sel_isect, non_sel_non_isect)))

    ea = pd.DataFrame.from_records([fisher_exact(x) for x in input], 
            index=C.columns, 
            columns=["Log2_Odds_Ratio", "P-Value"])
    ea["Log2_Odds_Ratio"] = np.log2(ea["Log2_Odds_Ratio"])

    ea["Hits"] = isect
    ea["Annotated"] = C.sum()
    ea = ea.ix[:,["Hits","Annotated","Log2_Odds_Ratio","P-Value"]].sort("Log2_Odds_Ratio", ascending=False)
    return ea.dropna()

def odds_ratio(K, A):
    """
    K - transcripts x conditions
    A - transcripts x annotation
    """
    K, A = K.align(A, join="inner", axis=0)
    transcripts = K.index
    conditions = K.columns
    annotations = A.columns
    # Kt = transposed K
    Kt, A = K.as_matrix().T, A.as_matrix()

    obs = np.dot(Kt, A) 
    p = np.outer(Kt.mean(axis=1), A.mean(axis=0)) 
    exp = p * len(transcripts)

    return pd.DataFrame(np.log2(np.divide(obs, exp)), 
            index=conditions, columns=annotations)
