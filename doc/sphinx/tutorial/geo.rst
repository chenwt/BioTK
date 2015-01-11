=============================================================
Tutorial 1: Downloading, preprocessing, and indexing GEO data
=============================================================

First, let's manually go through the steps to retrieve and preprocess a GEO
platform for analysis. We will see later that there are easier ways to do this
task, but this will give you a good flavor of how BioTK works.

The ``geo`` command contains multiple subcommands to download and process data
from NCBI GEO. Try typing it in the shell:

.. code-block:: bash
    
    $ geo

You will see a list of available subcommands.

Downloading MiniML files
------------------------

We will be working with the Affymetrix Human Genome U95A Array which has GEO
accession ``GPL91``, and approximately 1000 available samples.  You can
download the raw expression data for this platform using the command:

.. code-block:: bash

    $ geo fetch GPL91

This will download the data and create a file in your current directory called
``GPL91.miniml.tpxz``. The ``tpxz`` extension is an indexed TAR file,
created using the ``pixz`` utility. Normal TAR files only support sequential
access, but indexed TAR files support fast random access.

Extracting probe-level data
---------------------------

The first step to manipulating this data is to obtain a matrix of probes vs
sample accessions. This can be accomplished as follows:

.. code-block:: bash

    $ geo extract GPL91.miniml.tpxz | gzip > GPL91.probe.gz

The ``geo extract`` command extracts the data from the archive, whereas the
remainder of the command saves the result into a compressed file. Without the
latter part, the data would all be output into your terminal, which would be
overwhelming.

You can ensure that you got the matrix you expected by running this command:

.. code-block:: bash

    $ zcat GPL91.probe.gz | dt view

``zcat`` decompresses the file, whereas ``dt view`` views only the first few
rows and columns of the matrix. ``dt`` ("data manipulation tool"), like the
``geo`` command, is part of the BioTK suite and has multiple subcommands, which
you can view by typing ``dt`` by itself in the terminal.

More subcommands of ``dt`` will be introduced later, but generally speaking, it
contains various commands for conveniently working with tables and matrices in
a terminal environment.

Take a look at the distribution of values:

.. code-block:: bash

    # First probe

    $ zcat GPL91.probe.gz | cut -f2 | sed 1d | histogram

    # First sample

    $ zcat GPL91.probe.gz | transpose | cut -f2 | sed 1d | histogram

Collapsing probes to genes
--------------------------

Stanford maintains a set of files, called AILUN, that map array probes to
genes. We'll use BioTK's ``dataset`` tool to download this file and save it to
a file called ``probe2gene``:

.. code-block:: bash
    
    $ dataset ailun GPL91 > probe2gene 

These commands will save the mapping to a file that has two columns: the first
column is the probe ID, and the second is the Entrez Gene ID. Now, let's
collapse it to genes:

.. code-block:: bash

    $ zcat GPL91.probe.gz | dt collapse probe2gene | gzip > GPL91.gene.raw.gz

By default, the method used to collapse is the "max mean" method. You can see
more options by typing ``dt collapse``. Notice that this is a generic utility
that can collapse any kind of matrix based on a mapping file.

Take a look at your gene matrix:

.. code-block:: bash

    $ zcat GPL91.gene.raw.gz | dt view

Conditional log-transformation and normalization
------------------------------------------------

One problem in working with GEO data in a meta-analytic setting is that the
data can have many different kinds of normalization and pre-processing, or none
at all. There is no way to know, when processing at scale, what steps have been
done already, so we need to log-transform data that appears to be on a linear
scale, and renormalize it.

.. code-block:: bash

    $ zcat GPL91.gene.raw.gz \
        | dt transform -m 100 -b 2 log \
        | dt transform std \
        | gzip > GPL91.gene.nrm.gz

Instead of log-transforming all data, we only log-transform rows whose mean
value is greater than 100 (``-m 100``). This is obviously a heuristic, and you
can choose your own value, or if you omit the parameter, then all rows will be
log-transformed.

Standardization is the simplest form of normalization, and simply sets each row
to have a mean of zero and standard deviation of one. The advantage is that
each row can be considered independently of the others, which is not the case
for more complex methods like quantile normalization. For quantile
normalization, you can use the ``dt qnorm`` utility.

Note that we normalized after collapsing to genes, but many would argue that it
is preferable to normalize before collapsing.

BioTK design principles
-----------------------

So far, you have seen a few common principles that are relatively common
throughout the BioTK shell utilities:

- Commands are organized as pipelines, which take the data to be processed on
  standard input, and secondary files or parameters as command-line arguments 
  
- Whenever possible, the output of commands are printed to standard output (as
  opposed to saving them to a file), so that the results can be piped into
  further functions 
  
- Datasets are typically tab-delimited matrices or tables; i.e., they are a
  text format that can be processed by normal UNIX utilities
