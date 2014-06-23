from bottle import request

from BioTK.ui import root, render_template, Table
from BioTK import api

@root.get("/region")
def fn():
    return render_template("region.html", 
            title="Region Query (hg19)")

@root.post("/region")
def fn():
    params = dict(request.params.decode())
    taxon_id = 9606
    genome_build = "hg19"
    try:
        gene_id = int(params["gene_id"])
        table = api.region.region_expression_for_gene(
                taxon_id, genome_build, gene_id)
        title = "Correlated Genes - %s" % gene_id
    except (KeyError, ValueError):
        contig = params["contig"]
        start = int(params["start"])
        end = int(params["end"])
        table = api.region.region_expression(taxon_id, 
                genome_build, contig, start, end)
        title="Correlated Genes - %s:%s-%s" % \
                (contig, start, end)
    except TypeError:
        return "ERROR: locus could not be found gene ID: %s" % \
                (gene_id,)

    # ret two tables: coexpressed genes & predicted functions
    return render_template("tables.html",
            tables=[Table(table, 
                title=title,
                server_side=True)])
