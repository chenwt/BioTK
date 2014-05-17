"""
Lazily read BED files into BioTK.genome.Region objects.
"""
# TODO: currently fields past 6 are ignored

from BioTK.genome import Contig, GenomicRegion

from .common import generic_open

class BEDFile(object):
    def __init__(self, handle_or_path):
        self._handle = generic_open(handle_or_path)

    def __enter__(self):
        return self

    def __iter__(self):
        keys = ["contig", "start", "end", "name", "score", "strand"]
        NaN = float("NaN")

        for line in self._handle:
            if not line.strip():
                continue
            fields = line.strip().split("\t")
            attrs = dict(zip(keys, fields))
            contig = Contig(attrs["contig"])
            start = int(attrs["start"])
            end = int(attrs["end"])
            if "score" in attrs:
                try:
                    attrs["score"] = float(attrs["score"])
                except ValueError:
                    attrs["score"] = NaN
            yield GenomicRegion(contig, start, end, score=attrs.get("score", 0))

    def __exit__(self, *args):
        self._handle.close()

def parse(handle):
    return BEDFile(handle)
