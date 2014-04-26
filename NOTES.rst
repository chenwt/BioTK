Requirements
============

- xmlstarlet
- libarchive or the multi-threaded equivalent (pkgbuild: mtar-git)
- parallel
- BSD reshape (AUR: openbsd-rs-git) - TODO: patch to increase BUFSIZ
- cluster3 (pkgbuild: cluster3)
- vowpal wabbit
- lz4
- boost (iostreams)

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
