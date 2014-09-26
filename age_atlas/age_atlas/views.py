import json

from django.shortcuts import render
from django.http import HttpResponse

def execute(q, *args):
    c = db.cursor()
    if not args:
        c.execute(q)
    else:
        c.execute(q, tuple(args))
    return list(c)

import BioTK.db
db = BioTK.db.connect()
tissue_name_to_accession = dict(execute("""
    SELECT name,accession
    FROM term
    WHERE accession LIKE 'BTO:%'"""))
taxon_name_to_accession = dict(execute("""
    SELECT name,accession FROM taxon"""))

def view(template_name):
    def wrapper(fn, *args, **kwargs):
        def wrap(request):
            rs = fn(request, *args, **kwargs) or {}
            return render(request,
                    "age_atlas/%s.html" % template_name,
                    rs)
        return wrap
    return wrapper

@view("index")
def index(request):
    return

@view("tutorial")
def tutorial(request):
    return

@view("statistics")
def statistics(request):
    return {"tables": ["asdf", "ghjkl"]}

def autocomplete_tissue(request):
    c = db.cursor()
    c.execute("""
    SELECT t.id, t.name
    FROM term t
    INNER JOIN relation r
    ON r.object_id=t.id
    WHERE t.accession LIKE 'BTO:%'
    GROUP BY t.id
    ORDER BY COUNT(t.id) DESC
    """)
    tissues = [{"id":id,"name":name} for id,name in c]
    return HttpResponse(json.dumps(tissues, indent=4).replace("\n","\r\n"),
                        content_type="application/json")

def autocomplete_species(request):
    species = ["Homo sapiens", "Rattus norvegicus", "Mus musculus"]
    species = [{"name":n} for n in species]
    return HttpResponse(json.dumps(species, indent=4).replace("\n","\r\n"),
                        content_type="application/json")

def query_tissue(request):
    if request.method == "GET":
        return render(request, "age_atlas/query_tissue.html")
    elif request.method == "POST":
        p = request.POST
        taxon_id = taxon_name_to_accession[p["species"]]
        tissue_accession = tissue_name_to_accession[p["tissue"]]
        return HttpResponse(str((taxon_id,tissue_accession)))
