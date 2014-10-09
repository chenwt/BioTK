==============
BioTK tutorial
==============

This tutorial assumes BioTK has already been successfully installed.

The documentation for BioTK can be found at:

- http://wrenlab.org/code/BioTK/

BioTK contains shell utilities and Python APIs. In these tutorials, we'll
mostly focus on the shell utilities. The Python APIs can be used for more
custom tasks.

Tutorial 1: Downloading, preprocessing, and indexing GEO data
=============================================================

First, let's manually go through the steps to analyze a GEO platform. We will
see below that there are easier ways to do this task, but this will give you a
good flavor of how BioTK works.

The ``geo`` command contains multiple subcommands to download and process data
from NCBI GEO. Try typing it in the shell:

.. code-block:: bash
    
    $ geo

You will see a list of available subcommands.

Downloading MiniML files
------------------------

We will be working with the TaqMan qRT-PCR Homo sapiens Low-Density Array 380,
which has GEO accession ``GPL13728``, and approximately 370 available samples.
You can download the raw expression data for this platform using the command:

.. code-block:: bash

    geo fetch GPL13728

This will download the data and create a file in your current directory called
``GPL13728.miniml.tpxz``. The ``tpxz`` extension is an indexed TAR file,
created using the ``pixz`` utility. Normal TAR files only support sequential
access, but indexed TAR files support fast random access.

Extracting probe-level data
---------------------------

The first step to manipulating this data is to obtain a matrix of probes vs
sample accessions. This can be accomplished as follows:

.. code-block:: bash

    geo extract GPL13728.miniml.tpxz | gzip > GPL13728.probe.gz

The ``geo extract`` command extracts the data from the archive, whereas the
remainder of the command saves the result into a compressed file. Without the
latter part, the data would all be output into your terminal, which would be
overwhelming.

You can ensure that you got the matrix you expected by running this command:

.. code-block:: bash

    zcat GPL13728.probe.gz | dm view

``zcat`` decompresses the file, whereas ``dm view`` views only the first few
rows and columns of the matrix. ``dm`` ("data manipulation"), like the ``geo``
command, is part of the BioTK suite and has multiple subcommands, which you can
view by typing ``dm`` by itself in the terminal.

More subcommands of ``dm`` will be introduced later, but generally speaking, it
contains various commands for conveniently working with tables and matrices in
a terminal environment.

Collapsing probes to genes
--------------------------

Stanford maintains a set of files, called AILUN, that map array probes to
genes. BioTK has ways to retrieve this data automatically, but we'll retrieve
it manually and save it to a file called ``probe2gene``:

.. code-block:: bash
    
    curl ftp://ailun.stanford.edu/ailun/annotation/geo/GPL13728.annot.gz \
        | gzip -cd \
        | cut -f1-2 > probe2gene

These commands will save the mapping to a file that has two columns: the first
column is the probe ID, and the second is the Entrez Gene ID. Now, let's
collapse it to genes:

.. code-block:: bash

    zcat GPL13728.probe.gz | dm collapse probe2gene | gzip > GPL13728.gene.raw.gz

By default, the method used to collapse is the "max mean" method. You can see
more options by typing ``dm collapse``. Notice that this is a generic utility
that can collapse any kind of matrix based on a mapping file.

Take a look at your gene matrix:

.. code-block:: bash

    zcat GPL13728.gene.raw.gz | dm view

Conditional log-transformation and normalization
------------------------------------------------

One problem in working with GEO data in a meta-analytic setting is that the
data can have many different kinds of normalization and pre-processing, or none
at all. There is no way to know, when processing at scale, what steps have been
done already, so we need to log-transform data that appears to be on a linear
scale, and renormalize it.

.. code-block:: bash

    zcat GPL13728.gene.raw.gz | log-transform -r 100 | standardize | gzip > GPL13728.gene.nrm.gz

Instead of log-transforming all data, we only log-transform rows whose range
(max-min) is greater than 100 (``-r 100``). This is obviously a heuristic, and
you can choose your own value, or if you omit the parameter, then all rows will
be log-transformed.

Standardization is the simplest form of normalization, and simply sets each row
to have a mean of zero and standard deviation of one. The advantage is that
each row can be considered independently of the others, which is not the case
for more complex methods like quantile normalization. There is code for
quantile normalization in BioTK, but it currently does not have a command-line
utility.

Note that we normalized after collapsing to genes, but many would argue that it
is preferable to normalize before collapsing.

Indexed matrices ("xmat")
-------------------------

After the above few steps, we have an expression matrix that is ready for some
kinds of analysis. Tools for analysis will be covered in a later section.

Text matrices like the one we have created are just fine when you are only
analyzing dozens or hundreds of samples, but when dealing with the entirety of
GEO, they have a few drawbacks. Most importantly, they cannot be randomly
accessed; to pick out a single row, you have to iterate through the file until
you find the row you are looking for.

So, BioTK contains a tool, called ``xmat``, which allows you to store matrices
in an efficient file format and query any combination of rows and/or columns
you are interested in. To create one:

.. code-block:: bash

    zcat GPL13728.gene.nrm.gz | xmat load GPL13728.sample.xmat

This will create a file called ``GPL13728.sample.xmat``. Currently, ``xmat``
indexes matrices by row, so querying by row is much faster than querying by
column. If we want to have a matrix that we can use to efficiently query for
genes, we can do the following:

.. code-block:: bash

    zcat GPL13728.gene.nrm.gz | transpose | xmat load GPL13728.gene.xmat

Here we have introduced the self-explanatory ``transpose`` command. It can
handle arbitrarily large matrices by storing blocks on disk to perform the
transpose. (Almost all other available transposition tools only work in RAM,
which is a problem for huge matrices).

We can view the data in the xmat file:

.. code-block:: bash

    xmat dump GPL13728.gene.xmat | dm view

More interestingly, we can query it:

.. code-block:: bash
    
    # pick some random rows and columns
    xmat dump GPL13728.gene.xmat | cut -f1 | sed 1d | shuf | head > random-rows
    xmat dump GPL13728.gene.xmat | head -1 | tr '\t' '\n' | sed 1d | shuf | head > random-columns

    # get the submatrix containing only these rows and columns
    xmat query GPL13728.gene.xmat -r random-rows -c random-columns

In the future, ``xmat`` should be able to query both rows and columns with
equal efficiency using just one matrix file, but this is not yet implemented.
So, you should save your xmat such that the axis you query most often is the
rows.

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

Tutorial 2: Analyzing expression (and other) matrices
=====================================================

Correlation matrix
------------------

PCA
---

Tutorial 3: The "dataset" command
=================================

As you saw in Tutorial 1, transforming data from its original format into
something useful often takes multiple steps. It would get tedious to type in
those commands repeatedly, and the intermediate files could quickly clutter up
your working space.

The ``dataset`` command runs common data processing pipelines for you.
Moreover, it saves the intermediate results to speed up processing, in a
sensible directory structure. The location of this directory can be configured,
but by default it is ``$HOME/data``.

Take a look at the available datasets by typing ``dataset`` in the terminal.

Most of the datasets listed don't exist on your computer yet. If you run, for
example:

.. code-block:: bash

    dataset ontology-terms BTO | head

The necessary files will be downloaded to your computer before processing the
results. (The ``head`` command ensures only the first 10 records are output to
your terminal). 

Other ``dataset`` subcommands work in basically the same way; they output data
in a tab-delimited format, downloading files on the fly if necessary.

Tutorial 4: Text mining
=======================
