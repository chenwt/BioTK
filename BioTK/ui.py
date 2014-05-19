from os.path import join, dirname

import bottle
from bottle import route, template, static_file, view, request

import pandas as pd
import numpy as np

from BioTK import resource 

bottle.TEMPLATE_PATH.insert(0, resource.path("ui/template"))

root = bottle.Bottle()

########
# Routes
########

@root.route("/static/<path:path>")
def fn(path):
    return static_file(path, root=resource.path("ui/static"))

@root.route("/")
@view("index.tpl")
def fn():
    return 

@root.route("/expression")
@view("expression/index.tpl")
def fn():
    return

@root.get("/expression/region")
@view("expression/region.get.tpl")
def fn():
    return

@root.post("/expression/region")
@view("expression/region.post.tpl")
def fn():
    genome = request.forms.get("genome")
    region = request.forms.get("region")
    try:
        chrom, interval = region.split(":")[0]
        start, end = map(int, interval.split("-")) 
    except:
        pass
    table = pd.DataFrame(np.arange(15).reshape((5,3)), columns=["A","B","C"])
    return {"genome": genome, "region": region, "table": table}

if __name__ == "__main__":
    bottle.debug(True)
    bottle.run(root, reloader=True)
