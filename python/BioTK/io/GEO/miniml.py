"""
MiniML-based parser for GEO data (eventually to replace SOFT parser).
"""

import tarfile

from xml.etree import ElementTree

import pandas as pd

from BioTK.expression import ExpressionSet

__all__ = ["parse"]

class MiniMLExpressionSet(ExpressionSet):
    pass

NS = "{http://www.ncbi.nlm.nih.gov/geo/info/MINiML}"

def parse_xml(h):
    feature_attributes = {}
    characteristics = []
    sample_attributes = []

    tree = ElementTree.iterparse(h)
    for _, e in tree:
        if e.tag == NS+"Platform":
            gpl = e.attrib["iid"]
            tbl = e.find(NS+"Data-Table")
            records = []
            for col in tbl.findall(NS+"Column"):
                name = col.find(NS+"Name").text
                description = col.find(NS+"Description").text
                records.append((name, description))
            tbl = pd.DataFrame.from_records(records,
                    columns=["Name", "Description"])
            feature_attributes[gpl] = tbl

        elif e.tag == NS+"Sample":
            title = e.find(NS+"Title").text.strip()
            description = e.find(NS+"Description").text.strip()
            platform = e.find(NS+"Platform-Ref").attrib["ref"]

            channel_count = int(e.find(NS+"Channel-Count").text)
            # FIXME: allow channel_count > 1
            if channel_count != 1:
                raise Exception

            for ch in e.findall("Characteristics"):
                characteristics[ch.tag] = ch.text.strip()

        return platforms

def parse(path):
    with tarfile.open(path, "r:gz") as tgz:
        for ti in tgz:
            if not ti.isreg():
                continue
            h = tgz.extractfile(ti)
            if ti.name.startswith("GPL"):
                #tbl = pd.read_table(h, header=False)
                pass
            elif ti.name.startswith("GSM"):
                #tbl = pd.read_table(h, header=False).iloc[:,0]
                pass
            elif ti.name.endswith(".xml"):
                o = parse_xml(h)

if __name__ == "__main__":
    import sys
    parse(sys.argv[-1])
