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
from collections import namedtuple, defaultdict
import datetime
from pprint import pprint

import pandas as pd
import numpy

import BioTK.io.NCBI

def as_float(item):
    try:
        return float(item)
    except:
        return numpy.nan
        
def read_value(line):
    try:
        return line.strip().split(" = ", 2)[1]
    except IndexError:
        return ""

def as_int(attrs, key):
    v = attrs.get(key)
    if v is not None:
        return int(v.split("\n")[0]) 

def as_date(attrs, key):
    try:
        return datetime.datetime.strptime("%b %d %Y", attrs[key]).date()
    except:
        return

def split_lines(attrs, key):
    if key in attrs:
        return attrs[key].split("\n")

def identity(attrs, key):
    return attrs.get(key)

Database = namedtuple("Database", "name")
Platform = namedtuple("Platform", "accession,title,manufacturer,table")
Series = namedtuple("Series", 
    "accession,title,summary,design,type,submission_date,pubmed_id")
Sample = namedtuple("Sample", "accession,platform_accession,title,description,status,submission_date,last_update_date,type,hybridization_protocol,data_processing,contact,supplementary_file,channel_count,channels,table")
Channel = namedtuple("Channel", 
    "channel,taxon_id,source_name,characteristics,molecule,label,treatment_protocol,extract_protocol,label_protocol")

def _fix_attributes(cls, attrs):
    to_delete = set()
    for fk,tk,method in [
            ("taxid", "taxon_id", as_int), 
            ("pubmed_id", "pubmed_id", as_int),
            ("channel_count", "channel_count", as_int),
            ("submission_date", "submission_date", as_date),
            ("last_update_date", "last_update_date", as_date),
            ("hyb_protocol", "hybridization_protocol", identity),
            ("platform_id", "platform_accession", identity)
            ]:
        if fk in attrs:
            attrs[tk] = method(attrs, fk)
            to_delete.add(fk)
    for k in attrs.keys():
        if not k in cls._fields:
            to_delete.add(k)
    for k in to_delete:
        del attrs[k]
    for k in cls._fields:
        if not k == "accession":
            attrs.setdefault(k, None)

def _read_table(lines):
    lines = iter(lines)
    for line in lines:
        if line.strip().endswith("table_begin"):
            table_data = io.StringIO()
            for line in lines:
                if line.strip().endswith("table_end"):
                    break
                table_data.write(line)
            table_data.seek(0)
            return pd.read_table(table_data, index_col=0)
 
def _parse_attributes(cls, lines, fix=True):
    # attributes
    attrs = defaultdict(list)
    for line in lines:
        if not line.startswith("!"):
            continue
        try:
            key, value = line.strip().split(" = ", 1)
            key = key.split("_", 1)[1]
        except ValueError:
            pass
        attrs[key].append(value)
    attrs = dict((k, "\n".join(vs).strip()) for k,vs in attrs.items())

    # table
    attrs["table"] = _read_table(lines)

    if fix:
        _fix_attributes(cls, attrs)
    return attrs

def _parse_database(accession, lines):
    return Database(accession)

def _parse_platform(accession, lines):
    attrs = _parse_attributes(Platform, lines)
    return Platform(accession, **attrs)

def _parse_series(accession, lines):
    attrs = _parse_attributes(Series, lines)
    return Series(accession, **attrs)

def _parse_sample(accession, lines):
    attrs = _parse_attributes(Sample, lines, fix=False)
    channel_count = int(attrs["channel_count"])
    channels = []
    for i in range(1, channel_count+1):
        ch_attrs = {}
        for k,v in attrs.items():
            if k.endswith("_ch%s" % i):
                k = "_".join(k.split("_")[:-1])
                ch_attrs[k] = v
        _fix_attributes(Channel, ch_attrs)
        ch_attrs["channel"] = i
        channels.append(Channel(**ch_attrs))
    attrs["channels"] = channels
    _fix_attributes(Sample, attrs)
    return Sample(accession, **attrs)

def _parse(handle):
    lines = []
    for line in handle:
        if not line.startswith("^"):
            lines.append(line)
        else:
            if lines:
                try:
                    key = "_parse_" + type.lower()
                    handler = globals()[key]
                    yield handler(accession, lines)
                except KeyError as e:
                    print(e)
                    print("No handler found for type:", type)
            type, accession = line[1:].strip().split(" = ")
            lines = []

def parse(path):
    with gzip.open(path, "rt") as h:
        yield from _parse(h)
