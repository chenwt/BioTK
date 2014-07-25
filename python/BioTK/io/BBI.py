import argparse
import multiprocessing as mp
import os
import itertools
import subprocess as sp
import sys
import tempfile

import pandas as pd

from BioTK.io import BEDFile

class BigWigFile(object):
    def __init__(self, path):
        self.path = path

    def mean_single_locus(self, contig, start, end):
        cmd = ["bigWigSummary", self.path, chrom, start, end, 1]
        try:
            mu = float(sp.check_output(cmd, stderr=devnull)\
                    .strip()\
                    .decode("utf-8"))
            cmd.append("-type=coverage") 
            coverage = float(sp.check_output(cmd, stderr=devnull)\
                    .strip()\
                    .decode("utf-8"))
            return mu * coverage
        except:
            return np.nan

    def mean(self, regions):
        regions = list(regions)
        regions.sort(key=lambda rg: len(rg), reverse=True)
        regions = [next(rgs) for _, rgs in 
                itertools.groupby(regions, lambda rg: rg.name)]

        devnull = open(os.devnull, "w")
        with tempfile.NamedTemporaryFile("w") as h:
            for i,rg in enumerate(regions):
                print(rg.contig.name, rg.start, rg.end, i, sep="\t", file=h)
            h.flush()
            cmd = ["bigWigAverageOverBed", self.path, h.name, "stdout"]
            output = sp.check_output(cmd, stderr=devnull)
            output = output.strip().decode("utf-8")

        data = {}
        for line in output.split("\n"):
            if not line:
                continue
            fields = line.split("\t")
            index = int(fields[0])
            mu = float(fields[4])
            data[regions[index].name] = mu
        return pd.Series(data)

class BigWigCollection(object):
    def __init__(self, paths):
        self.files = [BigWigFile(path) for path in paths]

    def mean(self, regions):
        keys, series = [], []
        for f in self.files:
            key = os.path.splitext(os.path.basename(f.path))[0]
            rs = f.mean(regions)
            if rs is not None:
                keys.append(key)
                series.append(rs)
        return pd.DataFrame(series, index=keys)

if __name__ == "__main__":
    bwc = BigWigCollection(sys.argv[2:])
    regions = list(BEDFile(sys.argv[1]))
    bwc.mean(regions).to_csv(sys.stdout, sep="\t")
