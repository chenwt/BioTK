=================
BioTK Development
=================

Architecture & philosophy
=========================

The broad organizing principles of BioTK are as follows:

1. Write it as a shell script if possible. If that's not practical or too complex,
2. Then write it in Python, factoring things into reusable functions. If that is too slow,
3. First, try parallelizing it with GNU parallel. If it's still too slow,
4. Then write it in Cython or C++, as a last resort.

In any case, user-facing functions (executables) should follow the UNIX
philosophy, namely, each executable should:

- Do one thing well
- Be written as a "filter" (read from stdin, output to stdout)
- The only time an executable should produce something like a "log file" is if
  it is a daemon (e.g., a process that is going to run
  constantly/indefinitely). Long batch jobs should print output to stdout and
  logs/errors to stderr.
- Sometimes programs have to take more than one input, but they should very,
  very rarely produce more than one output (and that should be stdout).

Try to avoid inducing unnecessary dependencies, but if adding a dependency will
drastically shorten your workload, don't hesitate. Add it in the
requirements.txt (for a Python dependency) or binary-requirements.txt (for
native). Prefer Python dependencies to native dependencies.

How to contribute
=================

If you'd like to contribute to BioTK (yay!), please follow the guidelines
below. In summary:

1. Write the code
2. Write documentation
3. Write tests (that pass)
4. Submit a pull request

Although we use PEP8 for variable names and Numpy docstring format (with a few
exceptions), don't obsess over following every detail of these format guides,
especially if you are new to them. Just do what you can, and we can fix minor
errors later.

Writing code
============

Naming conventions
------------------

Code mostly follows standard Python naming conventions from PEP8
(lower_case_with_underscore for variables and functions, CamelCase for classes,
private variables or methods with leading underscore, etc.). 

**There is one exception**: modules and packages. Because of the huge
preponderance of acronyms in biomedicine, modules are CamelCase with acronyms
all uppercase if they describe a file format, external program, or well-known
algorithm. Otherwise, they are lower-case.

Examples:

- BioTK.io.BEDGraph
- BioTK.io.Aspera
- BioTK.text.parse
- BioTK.text.AhoCorasick

Documentation
=============

If you want to contribute some code, the most important kind of documentation
to provide is docstrings. Sphinx documentation and in-code comments are nice
to have, but not crucial.

Sphinx documentation
--------------------

High level information and tutorials are written in the doc/ directory in
reStructuredText format, and built into HTML and other formats using Sphinx.
These docs are automatically mirrored to http://BioTK.readthedocs.org/ .

A useful reStructuredText primer can be found at
http://docutils.sourceforge.net/docs/user/rst/quickref.html .

Docstrings
----------

Modules, and public classes and functions inside them, need docstrings. Keep
it high level, explaining *what* the module/function and the parameters are
doing, not *how* they are doing it. Provide citations to the algorithm's paper
if appropriate. Generally speaking, the more "public" a function/class is, the
more documentation it needs. If it should be rarely or never directly called
by a user, it may only need one line. Conversely, a large class with many
methods may need quite extensive documentation.

The docstrings are written in Numpy format, with one exception: in BioTK,
there is always a leading newline on the first line. Thus, instead of:

.. code-block:: python

    def add(a, b):
        """The sum of two numbers.

        (rest of docstring ...)
        """

we use:

.. code-block:: python

    def add(a, b):
        """
        The sum of two numbers.

        (rest of docstring ...)
        """

The numpy docstring format is described here:

- https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt

And many good examples are here:

- http://sphinx-doc.org/latest/ext/example_numpy.html

Internal code comments
----------------------

Functions and class methods should be short enough, and the code should be
clear enough, that code comments should mostly be unnecessary. Use good
judgment: if a particularly tricky method is being used, it may need some
explanation, but in general keep comments high level.

You can mark "wishlist" items with a TODO comment, and items that are actually
broken or need urgent attention with "FIXME" (obviously the latter should be
done sparingly).

Unit tests
==========

They are written using the py.test framework, and are placed in the test/
directory, with a directory structure that mirrors the structure of BioTK.

If possible, avoid tests that take a long time to run or require network
access.
