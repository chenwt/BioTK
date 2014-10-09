=================================
Welcome to BioTK's documentation!
=================================

Overview
========

BioTK is a Python toolkit, containing a library and scripts, for various
bioinformatics tasks:

- Meta-analysis and differential expression analysis of microarray and RNA-seq data
- Functional and downstream analysis of DE gene lists
- Ontology handling 
- Text mining, ranging from shallow NLP to relation extraction
- Efficient storage and querying of sets of genomic intervals 
  (similar to BEDTools, GenomicRanges, etc.)
- Generic data manipulation on the command-line

Getting Started
===============

.. toctree::
    :maxdepth: 2

    install
    configuration

Tutorials
=========

BioTK contains shell utilities and Python APIs. In these tutorials, we mostly
focus on the shell utilities. The Python APIs can be used for more custom
tasks.

.. toctree::
    :maxdepth: 2

    tutorial/geo
    tutorial/matrix-analysis
    tutorial/dataset
    tutorial/text-mining
    tutorial/genome

Manual
======

.. toctree::
    :maxdepth: 2

    datasets

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
