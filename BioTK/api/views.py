import io
import functools

from django.shortcuts import render, HttpResponse
import pandas as pd

import BioTK.db
from BioTK.mmat import MMAT
from BioTK.db.matrix import get_matrix

db = BioTK.db.connect()

def view(template_name):
    def wrapper(fn, *args, **kwargs):
        def wrap(request):
            rs = fn(request, *args, **kwargs) or {}
            return render(request,
                          "BioTK/api/%s.html" % template_name,
                          rs)
        return wrap
    return wrapper

def frame_to_response(df, index=False):
    with io.StringIO() as h:
        df.to_csv(h, float_format="%0.3f", sep="\t", index=index)
        return HttpResponse(h.getvalue().replace("\n", "\r\n"),
                            content_type="text/plain")

def view_frame(fn):
    @functools.wraps(fn)
    def wrap(*args, **kwargs):
        df = fn(*args, **kwargs)
        return frame_to_response(df)
    return wrap

def view_sequence(fn):
    @functools.wraps(fn)
    def wrap(*args, **kwargs):
        rs = fn(*args, **kwargs)
        return HttpResponse("\r\n".join(map(str, rs)),
                            content_type="text/plain")
    return wrap

def view_query(fn):
    @functools.wraps(fn)
    def wrap(*args, **kwargs):
        q, *params = fn(*args, **kwargs)
        params = params or None
        df = pd.io.sql.read_sql_query(q, db, params=params)
        return frame_to_response(df)
    return wrap

@view("index")
def index(request):
    return

@view_frame
def matrix_gene(request, taxon_id, type, gene_id):
    m = get_matrix(taxon_id, raw=type=="raw", index="gene")
    return m.loc[int(gene_id), :]

@view_frame
def matrix_sample(request, taxon_id, type, sample_accession):
    m = get_matrix(taxon_id, raw=type=="raw")
    return m.loc[sample_accession, :]

@view_sequence
def matrix_list(request, taxon_id, type, index):
    return get_matrix(taxon_id, raw=type=="raw", index=index).index

@functools.lru_cache()
def gene_info(taxon_id):
    return pd.io.sql.read_sql_query("""
        SELECT g.accession::int as "Gene ID",
            g.symbol as "Symbol",
            g.name as "Name"
        FROM gene g
        INNER JOIN taxon t
        ON t.id=g.taxon_id
        WHERE t.accession='{}'""".format(taxon_id), db,
                                    index_col="Gene ID")
def control_for(X, groups):
    # index = sample
    # column = gene
    return X.mean() + X.groupby(groups).transform(lambda g: g - g.mean())

def tissue_age_correlation(request, taxon_id, tissue):
    m = get_matrix(taxon_id, raw=False, index="sample")
    meta = pd.io.sql.read_sql_query("""
        SELECT channel_accession as "Sample",
            series_accession as "Series",
            age as "Age",
            gender as "Gender"
        FROM channel_attribute
        WHERE taxon_accession='{}'
        AND tissue_accession='{}'""".format(taxon_id,tissue), db)\
        .drop_duplicates(subset=["Sample"])
    meta.index = meta["Sample"]
    age = meta["Age"]
    series = meta["Series"]

    ix = set(age.index) & set(m.index)
    X = m.loc[ix, :].to_frame().dropna(axis=1, thresh=10)

    # Normalize for series and gender
    X = control_for(X, meta["Series"])
    X = control_for(X, meta["Gender"])

    o = X.corrwith(age).dropna().to_frame("r")
    o["N"] = (~X.isnull()).sum()
    o.index.name = "Gene ID"
    o = gene_info(taxon_id).join(o, how="right")
    o = o.sort("r")
    return frame_to_response(o, index=True)

@view_query
def tissue_list(request):
    return """
        SELECT accession, name
        FROM term
        WHERE term.accession LIKE 'BTO:%'""",

@view_query
def test(request):
    return "SELECT channel_accession FROM channel_attribute limit 5",

def not_implemented(request, *args, **kwargs):
    return HttpResponse("not implemented")
