import os

import pandas as pd

from BioTK import CONFIG
from BioTK.io.BBI import BigWigFile

class RNASeqDataset(object):
    """
    A collection of RNA-seq BigWig files from the same genome build.
    """
    def __init__(self, taxon_id, genome_build, dir):
        self.taxon_id = taxon_id
        self.genome_build = genome_build
        self.dir = dir
        self._handles = {}
        for file in os.listdir(dir):
            if file.endswith(".bw"):
                path = os.path.join(dir, file)
                id = os.path.splitext(os.path.basename(path))[0]
                self._handles[id] = BigWigFile(path)

    def expression(self, chrom, start, end):
        row = {}
        for id, bw in self._handles.items():
            row[id] = bw.summarize_region(chrom, start, end)
        return pd.Series(row)

    def coexpressed_transcripts(self, chrom, start, end):
        pass

if False:
    # If the RNA-Seq data path is configured and exists,
    # find out which datasets are available 
    RNASeq = {}
    root = CONFIG["data.rnaseq.dir"]
    if not os.path.isabs(root):
        root = os.path.join(CONFIG["data.root.dir"], root)
    if os.path.exists(root):
        for taxon_id in os.listdir(root):
            taxon_dir = os.path.join(root, str(taxon_id))
            if not os.path.isdir(taxon_dir):
                continue
            try:
                taxon_id = int(taxon_id)
            except ValueError:
                pass

            RNASeq.setdefault(taxon_id, {})
            for genome_build in os.listdir(taxon_dir):
                dir = os.path.join(taxon_dir, genome_build)
                RNASeq[taxon_id][genome_build] = RNASeqDataset(taxon_id, genome_build, dir)
