============================================================
Tutorial 2: Analyzing matrices (e.g., expression, comention)
============================================================

Correlation & distance matrices
===============================

Finding the correlation between all columns in a matrix, or finding the top N
most correlated columns, requires the ``dm correlate`` command. Starting from
where we left off in Tutorial 1:

.. code-block:: bash

    $ xmat query -r random-rows -c random-columns GPL91.gene.xmat > small.tsv

    # For each gene (column), find the top 5 most correlated genes
    # The first column is the "query" column, and the subsequent N
    #   columns are the top correlated column names.
    $ dm correlate -n 5 < small.tsv

    # Print out the full correlation matrix (between columns)
    $ dm correlate -a < small.tsv

    # Between rows, with 3 digits after the decimal
    $ transpose < small.tsv | dm correlate -a -d 3

Not yet implemented is the ability to use different distance metrics or print
out the top anticorrelated columns. Other planned improvements include
parallelism, the ability to correlate out-of-core matrices, and to correlate a
matrix with an externally-provided vector or matrix.

(N.B., This command may soon be renamed to ``dm distance`` once other metrics
are implemented).

TODO
====

- PCA
- Enrichment analysis (order-based [GSEA-like] and set-based [GOEA-like])
- Multivariate models & partial correlations
- All-in-one group comparison and EA scripts for vanilla microarray factor and regression models
