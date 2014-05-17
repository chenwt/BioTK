"""
Fetch and parse SOFT files from NCBI's GEO (Gene Expression Omnibus), returning
information about gene expression experiments and mappings of probes to target
genes.
"""

# TODO: replace the ad-hoc parsing with pyparsing (see grammar.py)

import base64
import collections
import gzip
import itertools
import io
import os
import re
import sys
import urllib.request

import pandas as pd
import numpy

import BioTK.io.NCBI

def as_float(item):
    try:
        return float(item)
    except:
        return numpy.nan
        
def read_table(lines, end_tag):
    buffer = io.StringIO()
    for line in lines:
        if line.startswith(end_tag):
            buffer.seek(0)
            return pd.io.parsers.read_csv(buffer, sep="\t")
        buffer.write(line)

def read_value(line):
    try:
        return line.strip().split(" = ", 2)[1]
    except IndexError:
        return ""

class GSM(object):
    """
    Represents a single GEO sample.
    """
    _columns = ["title", "supplementary_file", "table",
            "hyb_protocol", "scan_protocol", "data_processing",
            "description", "platform_id", "geo_accession",
            "anchor", "type", "tag_count", "tag_length"]
    _channel_columns = ["source_name", "organism", "characteristics",
            "biomaterial_provider", "treatment_protocol",
            "growth_protocol", "molecule",
            "extract_protocol", "label",
            "label_protocol"]

    #for col in sample_channel_columns:
    #    sample_columns.append(col + "_ch1")


    def __init__(self, accession, expression, attributes=None):
        self.accession = accession
        self.expression = expression
        self.attributes = attributes

    def __repr__(self):
        return "<Sample: %s>" % self.accession
        
class GPL(object):
    """
    Object containing information about a GEO platform and 
    mapping of probes to other accessions.
    """
    __slots__ = ["accession", "taxon_id", "organism", "title", "table"]

    def __init__(self, accession, taxon_id, organism, title, table):
        self.accession = accession
        self.taxon_id = taxon_id
        self.organism = organism
        self.title = title
        self.table = table.set_index("ID")

    def __repr__(self):
        return "<Platform description: %s - %s>" % (self.accession, self.title)

    @staticmethod
    def parse(handle):
        # FIXME: the taxon ID is not listed in the .annot.gz file
        for line in handle:
            line = line.strip()
            if line.startswith("!Annotation_platform ="):
                accession = read_value(line)
            elif line.startswith("!Annotation_platform_title"):
                title = read_value(line)
            elif line.startswith("!Annotation_platform_organism"):
                organism = read_value(line)
            elif line.startswith("!platform_table_begin"):
                table = read_table(handle, "!platform_table_end")
        try:
            return GPL(accession, None, organism, title, table)
        except NameError:
            raise IOError("Could not parse platform SOFT file.")

    @staticmethod
    def fetch(accession):
        assert accession.startswith("GPL")
        url = "/geo/platforms/GPL%snnn/%s/annot/%s.annot.gz" % \
                (accession[3:-3], accession, accession)
        with BioTK.io.NCBI.download(url, decompress="gzip") as handle:
            return GPL.parse(handle)

"""
class GSE(object):
    @staticmethod
    def fetch(accession):
        assert accession.startswith("GSE")
        url = "/geo/series/GSE%snnn/%s/matrix/
"""

class Family(object):
    """
    A class to read from whole-platform SOFT datasets, such
    as those found at ftp://ftp.ncbi.nlm.nih.gov/geo/platforms/ . 

    It assumes the platform data will precede the samples.
    """
    def __init__(self, platform, samples, expression):
        self.platform = platform
        self.samples = samples
        self.expression = expression

    @property
    def accession(self):
        return self.platform.accession

    def __repr__(self):
        return "<Family %s with %s samples>" % \
                (self.accession, self.expression.shape[0])

    @staticmethod
    def _parse_platform(handle):
        while True:
            line = handle.__next__()
            if line.startswith("!platform_table_begin"):
                table = read_table(handle, "!platform_table_end")
                break
            elif line.startswith("!Platform_taxid"):
                taxon_id = int(read_value(line))
            elif line.startswith("!Platform_title"):
                title = read_value(line)
            elif line.startswith("!Platform_organism"):
                organism = read_value(line)
            elif line.startswith("!Platform_geo_accession"):
                accession = read_value(line)
        return GPL(accession, taxon_id, organism, title, table) 

    _TRANSFORMERS = {
            "channel_count": int,
    }

    @staticmethod
    def _parse_single(handle):
        platform = Family._parse_platform(handle)
        yield platform

        while True:
            try:
                line = handle.__next__().strip()
                if line.startswith("^SAMPLE"):
                    attrs = collections.defaultdict(str)
                    accession = read_value(line)

                elif line.startswith("!Sample_"):
                    key = line.split(" = ")[0].lstrip("!Sample_")
                    value = read_value(line)
                    attrs[key] += value + "\n"
                elif line.startswith("!sample_table_begin"):
                    expression = read_table(handle, "!sample_table_end")
                    expression = expression.set_index("ID_REF")["VALUE"]
                    if expression.dtype != float:
                        expression = pd.Series(list(map(as_float, expression)), 
                            index=expression.index)

                    for k,v in attrs.items():
                        attrs[k] = v.strip()
                        if k in Family._TRANSFORMERS:
                            attrs[k] = Family._TRANSFORMERS[k](v)
                    yield GSM(accession, expression, 
                            attributes=dict(attrs.items()))
            except StopIteration:
                break
            except Exception as e:
                print(e)
                continue

    @staticmethod
    def parse(handle, limit=0, chunk_size=100):
        # FIXME: make sure platform/probes have same alignment
        # in all chunks
        it = Family._parse_single(handle)
        platform = it.__next__()
        if limit:
            it = itertools.islice(it, 0, limit)

        for gsms in BioTK.util.chunks(it, chunk_size):
            accessions = [gsm.accession for gsm in gsms]
            samples = [gsm.attributes for gsm in gsms]
            expression = [gsm.expression for gsm in gsms]

            samples = pd.DataFrame.from_records(samples, index=accessions)
            expression = pd.DataFrame(expression, index=accessions)
            platform_table = platform.table.T
            platform_table, expression = \
                    platform_table.align(expression, axis=1, join="left")
            platform.table = platform_table.T
            yield Family(platform, samples, expression)

    @staticmethod
    def fetch(accession):
        assert accession.startswith("GPL")
        url = "/geo/platforms/GPL%snnn/%s/soft/%s_family.soft.gz" % \
                (accession[3:-3], accession, accession)
        with BioTK.io.NCBI.download(url, decompress="gzip") as handle:
            return Family.parse(handle, chunk_size=0).__next__()

def fetch(accession):
    if accession.startswith("GSE"):
        return GSE.fetch(accession)
    elif accession.startswith("GPL"):
        return GPL.fetch(accession)
