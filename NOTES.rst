Interesting Packages
====================

- owltools (pkgbuild: owltools)
- csvkit (AUR: csvkit-git)

TODO
====

- Add (or use) a $DELIMITER environment variable if it is defined
- Add djoin (join with using column names and skipping header rows and optional built-in sort on key columns)

Links
=====

- http://jeroenjanssens.com/2013/09/19/seven-command-line-tools-for-data-science.html

Expression processing pipeline
==============================

The current implementation is:

1. Fetch and extract raw per-probe expression from GEO (geo-fetch and 
   geo-extract-expression)

2. Use ailun probe to Entrez mappings, collapse to genes and normalize 
   (collapse-to-genes):
   - collapse probes to genes by geometric mean
   - convert expression to log2 values (attempting to 
     detect whether already on a log scale)
   - normalize each sample to a standard (mean=0, sd=1) 
     log-normal distribution

3. Import all the desired platforms into one HDF5 matrix per species
   (h5-import-matrix). The columns are the set of all Entrez Gene IDs for that
   species.

4. Renormalize by gene so that each gene has a standard normal distribution

- PMID12016055 is a good reference for the fact that probe intensity can be
  well approximated by a log-normal distribution. (It also says power law fits
  better on the long tail).

Improvements/TODOs
------------------

- should detect whether each sample is log scale before collapsing?

- control or check for whether there are platform biases in expression
  resulting from the collapsing

Snippets
========

Making a template from expression matrix::

    lz4 -d GPL1234.expr.lz4 \
        | normalize-expression \
        | transpose -m \
        | vw-make-template \
        | lz4 > GPL1234.tmpl.lz4

Extracting the GPL from a MiniML archive::

    gpl=$(bsdtar -q -xOf ${archive} '*_family.xml' \
        | xml sel -T -t -v '//_:Platform/@iid' \
        | head -1)

Getting id-name mappings from an OBO/OWL::

    owltools http://purl.obolibrary.org/obo/bto.owl \
        --object-to-label-table \
        | sed 's/^[^BTO]*BTO_/BTO:/'

Getting parent-child relationships from OBO/OWL::

    owltools http://purl.obolibrary.org/obo/bto.owl \
        --write-all-subclass-relationships
