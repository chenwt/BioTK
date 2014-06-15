import os
import functools
import json
import random
import io

import numpy as np
import pandas as pd
import bottle
from nltk.metrics import edit_distance
from scipy import stats
from bottle import request, response, redirect

from BioTK.db import *
from BioTK.ui import root, db, render_template, Table
from BioTK.data import GeneOntology

import BioTK.api as api

# FIXME FIXME FIXME:
# - figure out why big difference b/t pearsonr and corrwith 
#   (well, b/t plot_gene and age_correlation)

# FIXME:
# - make downloaded files have appropriate filename 
#   and be filtered (rather than downloading whole table)
# - make a default require js main

@root.route("/query")
def fn():
    # FIXME
    tissues = list(api.tissue_counts.delay(9606).get().index[:15])
    return render_template("query.html", 
            tissues=tissues,
            title="Advanced Query")

@root.post("/api/table/<uuid>")
def fn(uuid):
    params = dict(request.params.decode())
    table = Table.cache[uuid]
    return table.ajax(params)

@root.get("/api/table/<uuid>/csv")
def fn(uuid):
    buffer = io.StringIO()
    Table.cache[uuid].data.to_csv(buffer)
    response.content_type = "application/csv"
    response.set_header("Content-Disposition", 
            "attachment; filename=age_atlas.csv")
    return buffer.getvalue()

@root.post("/gene-table")
def fn():
    taxon_id = int(request.forms["taxon_id"])
    tissue = request.forms["tissue"]
    table, sample_count = \
            api.tissue_age_correlation.delay(taxon_id, tissue).get()
    table = Table(table, server_side=True)
    return render_template("tables.html", 
            title="%s - %s (%s samples used)" % \
                (db.query(Taxon).get(taxon_id).name,
                    tissue, sample_count),
            tables=[table])

"""
tissues.extend(["B cell", "T cell"])
xtissues = ["neuron", 
        "temporal cortex",
        "frontal cortex",
        "parietal cortex",
        "occipital cortex", 
        "hippocampus",
        "CA1",
        "CA2",
        "CA2",
        "cerebellum",
        "cerebrospinal fluid",
        "neocortex"]
"""

def set_default_taxon(taxon_id):
    response.set_cookie("default_taxon_id", str(taxon_id))

def get_default_taxon():
    return int(request.get_cookie("default_taxon_id", "9606"))

def sort_by_distance(df, column, q):
    pass

def search_genes(q):
    # An Entrez Gene ID?
    try:
        gene_id = int(q)
        return "/gene/%s" % gene_id
    except:
        pass

    # Otherwise, search the text of gene symbols, names, and terms
    rows = [(g.id, g.symbol, g.taxon.name, g.name)
        for g in 
        db.query(Gene)\
                .filter(Gene.symbol.ilike("%"+q+"%"))]
    if len(rows) >= 1:
        df = pd.DataFrame.from_records(rows,
                columns=["Gene ID", "Symbol", "Species", "Name"])\
                        .dropna()
        df["Gene ID"] = df["Gene ID"].astype(int)
        if len(rows) > 1:
            def distance(ix):
                symbol = df["Symbol"].loc[ix]
                return edit_distance(symbol.lower(), q.lower())
            df = df.reindex_axis(list(map(distance, df.index)),
                axis=0).drop_duplicates(cols=["Gene ID"])
        return df

def search_terms(q):
    # A GO term?
    if q.lower().startswith("go:"):
        try:
            original_id = int(q[3:])
            term_id = db.query(Term)\
                    .join(Ontology)\
                    .filter(Ontology.abbreviation=="GO",
                            Term.original_id==original_id)\
                                    .first().id
            return "/term/%s/%s" % (get_default_taxon(), term_id)
        except Exception as e:
            print(e, file=sys.stderr)

    rows = []
    for t in db.query(Term).filter(Term.name.ilike("%" + q + "%")):
        rows.append((t.id, t.accession, t.name))
    df = pd.DataFrame.from_records(rows,
            columns=["Term ID", "Accession", "Name"])
    # FIXME: sort by edit distance
    return df

@root.post('/search')
def search():  
    q = request.forms["query"]
    if len(q) < 2:
        return

    genes = search_genes(q)
    terms = search_terms(q)
   
    if genes is None and terms is None:
        msg = "<h3>Sorry, no results found for query: '%s'</h3>" % q
        return render_template("base.html", content=msg)
    elif isinstance(genes, str):
        redirect(genes)
    elif isinstance(terms, str):
        redirect(terms)
    else:
        tables = []
        if genes is not None:
            tables.append(Table(genes,
                title="Genes",
                link_format="/gene/{0}",
                server_side=True))
        if terms is not None:
            tables.append(Table(terms,
                    title="Terms",
                    link_format="/term/{0}",
                    server_side=True))
        return render_template("tables.html", title="Search Results",
            tables=tables)

@root.get('/statistics')
def statistics():
    expression_counts = api.statistics.delay().get()
    tables = [Table(expression_counts, 
        title="Expression datasets",
        link_format="/statistics/{0}")]

    return render_template("tables.html", 
            title="Database statistics",
            tables=tables)

@root.get('/statistics/<taxon_id>')
def taxon_statistics(taxon_id):
    df = api.taxon_statistics.delay(taxon_id).get()
    tables = [Table(df, title="Common tissues")]
    return render_template("tables.html", tables=tables)

@root.get('/term/<term_id>/<taxon_id>')
def go_term(taxon_id, term_id):
    taxon_id, term_id = int(taxon_id), int(term_id)
    taxon = db.query(Taxon).get(taxon_id)
    term = db.query(Term).get(term_id)
    genes = []
    for annotation in db.query(GeneAnnotation)\
                .join(Gene)\
                .join(Term)\
                .filter(Gene.taxon_id==taxon_id,
                        Term.id==term_id):
        genes.append(annotation.gene_id)
    if not genes:
        # TODO: Would you like to try again with predicted functions?
        return render_template("base.html",
                content="Sorry, no genes are annotated in %s with '%s'." % \
                    (taxon.name, term.name))
    return plot_gene_set(taxon_id, genes, 
            title="%s - %s (%s; %d genes)" % 
            (term.accession, term.name, taxon.name, len(genes)))

def plot_gene_set(taxon_id, genes, title=""):
    """
    Plot various characteristics of a gene or gene set compared
    with age and subsetted by tissue.
    """
    genes = tuple(genes)
    result = api.gene_set_age_analysis(taxon_id, genes)
    if result is None:
        return render_template("base.html", 
                content="Sorry, no data for gene set: %s" % str(genes))
    Z = result["expression"].copy()
    if taxon_id == 9606:
        Z["Age"] = Z["Age"] / 12
    expression = []
    for t in Z["Tissue"].unique():
        df = Z.ix[Z["Tissue"] == t,:]
        values = []
        for i in range(df.shape[0]):
            values.append({
                "x": df["Age"].iloc[i], 
                "y": df["Expression"].iloc[i], 
                "id": str(df.index[i]),
                "size": 2})
        # Workaround for a bug in NVD3 scatter plot labeling
        t = t + (" " * (len(t) - 2))
        expression.append({"key": t, "values": values})
    tissue = result["tissue"].dropna()
    tissue["Tissue"] = tissue.index

    age_units = "years" if taxon_id == 9606 else "months"

    return render_template('plot_gene.html',
            age_units=age_units,
            title=title,
            expression=json.dumps(expression),
            js_main="plot-gene",
            tissue_json=json.dumps(list(tissue.T.to_dict().values())))

@root.get("/term/<term_id>")
def fn(term_id):
    term_id = int(term_id)
    term = db.query(Term).get(term_id)
    rows = []
    for taxon in db.query(Taxon):
        n = db.query(Gene)\
                .join(GeneAnnotation)\
                .filter(Gene.taxon_id==taxon.id,
                        GeneAnnotation.term_id==term_id)\
                                .count()
        rows.append((taxon.id, taxon.name, n))

    tables = [Table(pd.DataFrame.from_records(rows,
        columns=["Taxon ID", "Species", "Genes Annotated"]),
        link_format="/term/%s/{0}" % term_id)]
    title = "%s - %s" % (term.accession, term.name)
    return render_template("tables.html",
            tables=tables, title=title)

@root.get('/gene/<gene_id>')
def plot_gene(gene_id):
    gene = db.query(Gene).get(int(gene_id))
    return plot_gene_set(gene.taxon_id, [gene_id],
            title="%s - %s (%s)" % (gene.symbol, gene.name, gene.taxon.name))

@root.get("/sample/<sample_id>")
def fn(sample_id):
    sample_id = int(sample_id)
    sample = db.query(GEOSample).get(sample_id)
    tables = [
            Table(pd.DataFrame.from_records([
                ("Tissue", "not implemented", 0.99),
                ], columns=["Field", "Label", "Probability"]),
                title="Attributes"),
            Table(pd.DataFrame.from_records([
                ("Title", sample.title),
                ("Description", sample.description),
                ("Source", sample.source),
                ("Characteristics", sample.characteristics)
            ], columns=["Field", "Value"]),
            title="Investigator Description")
    ]
    title = "GSM%s" % sample.id
    return render_template("tables.html", title=title, tables=tables)
