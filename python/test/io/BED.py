import os

import pytest

from BioTK import data_path
from BioTK.io import BEDFile

base_dir = data_path("io/BED")

@pytest.mark.parametrize("file,count", [
        ("bed3.bed", 1),
        ("bed4.bed", 1),
        ("bed5.bed", 1),
        ("bed6.bed", 1),
        ("bed6.strand.bed", 1),
        ("bed6.strand2.bed", 2),
        ("bedplus.bed", 1),
        ("empty.bed", 0),
        ("non-empty.bed.gz", 2)
])
def test_read_bed(file, count):
    path = os.path.join(base_dir,file)
    with BEDFile(path) as handle:
        assert(len(list(handle)) == count)
