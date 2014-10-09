=================================
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
