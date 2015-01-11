===================
Sequencing analysis
===================

BioTK has tools for meta-analysis of sequencing data, focusing on RNA-seq.
Using these tools requires a data directory with a defined layout (see the
section `Sequencing data layout`_ for more information). On Wren Lab servers,
the tools will find and use this directory automatically.

Region queries
==============

BioTK installs a script called ``region-query``, which can be used to find
counts for a given locus, or correlations between a given locus and other
genes/transcripts in that genome. Run ``region-query --help`` for usage
information.

Sequencing data layout
======================

To use these tools, a directory containing various sequencing-related data is
needed. This includes reference genomes, aligner indexes, gene loci, and more.
Currently, these data have to be downloaded and the directory structure
assembled manually, but this will be automated in the future. For now, this
section describes the layout.

The base sequencing directory contains the following subdirectories:

- ``reference/`` : This contains genome builds in FASTA format, with each file
  having the name $BUILD_NAME.fa.

- ``index/`` : This contains several subdirectories for each aligner; e.g.,
  STAR, bowtie, bowtie2, etc. The folder content is aligner-specific, but in
  the base of bowtie(1/2) contains built indexes with prefixes corresponding to
  the genome build name, and symlinks to the appropriate FASTA files (in the
  reference/ directory)

- ``reads/`` : Contains subdirectories named after NCBI taxon IDs, containing
  FASTQ and possibly .sra files, with the prefix of the file name corresponding
  to the ID of the sample.

- ``align/`` : Contains subdirectories named after the genome build (e.g.,
  "GRCh38.p3"), containing BAM-format alignments, BigWig-format alignment depth
  summaries, and transcript counts. For BAM files, the prefix is the sample ID.
  For BigWig files, there are two subdirectories "+" and "-" containing data
  for each strand with prefixes corresponding to the sample ID. For transcript
  counts (".cf", ".count" for binary and text formats, respectively, created by
  RNAStar), the name is "sampleID.transcriptSource.extension", where
  "transcriptSource" can be "enst" (Ensembl Transcript), "eg" (Entrez Gene),
  etc.
