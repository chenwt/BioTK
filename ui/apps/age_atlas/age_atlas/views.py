from django.shortcuts import render
from django.http import HttpResponse

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

def query_tissue(request):
    if request.method == "GET":
        return render(request, 
                "age_atlas/query_tissue.html", {})
    elif request.method == "POST":
        p = request.POST
        taxon_id = int(p["taxon_id"])
        return HttpResponse(str(taxon_id))
