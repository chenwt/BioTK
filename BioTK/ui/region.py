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
    contig = params["contig"]
    start = int(params["start"])
    end = int(params["end"])
    table = api.region.region_expression(taxon_id, genome_build,
            contig, start, end)

    # ret two tables: coexpressed genes & predicted functions
    return render_template("tables.html",
            title="Correlated Genes - %s:%s-%s" % \
                    (contig, start, end),
            tables=[Table(table, 
                server_side=True)])
