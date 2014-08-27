=================================
Welcome to BioTK's documentation!
=================================

Overview
========

BioTK is a Python toolkit, containing a library and scripts, for various
bioinformatics tasks:

- Differential expression analysis on microarray and RNA-seq data
- Functional and downstream analysis of DE gene lists
- Ontology handling 
- Text mining, ranging from shallow NLP to relation extraction
- Efficient storage and querying of sets of genomic intervals 
  (similar to BEDTools, GenomicRanges, etc.)

BioTK is also a framework for integration of heterogeneous biomedical data.
For these components, it contains schemas, loaders, and queries for a backend
Neo4j graph database, distributed tasks for loads and queries via Celery,
caching and locking via Redis, and a web interface.

Tutorial
========

.. toctree::
    :maxdepth: 2

    expression
    meta-analysis
    framework

Development information
=======================

.. toctree::
    :maxdepth: 3

    dev
    hacking

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
