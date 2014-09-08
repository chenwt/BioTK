import os
import sys
import gzip
from os.path import join, dirname
from functools import partial
from subprocess import Popen, PIPE
import tempfile

from bottle import Bottle, run, request, response
from jinja2 import Environment, FileSystemLoader

import BioTK.db

api = Bottle()
template_dir = join(dirname(__file__), "tmpl")
env = Environment(loader=FileSystemLoader(template_dir))
db = BioTK.db.connect()

def view(tmpl):
    def wrapper(fn):
        def wrap(*args, **kwargs):
            rs = fn(*args, **kwargs)
            return env.get_template(tmpl).render(**rs)
        return wrap
    return wrapper

@api.get("/")
@view("index.html")
def index():
    return {"title": "Wren Lab Data API"}

@api.get("/matrix")
@view("matrix.html")
def matrix():
    c = db.cursor()
    c.execute("""
    SELECT name,accession 
    FROM term 
    WHERE accession LIKE 'BTO:%'""")
    tissues = list(sorted(c))
    return {
            "title": "GEO Matrix Query",
            "taxa": [
                ("Homo sapiens", 9606)
            ],
            "tissues": tissues
        }

@api.post("/matrix")
def matrix():
    q = dict(request.forms)
    cmd = ["geo", "select"]
    if q["normalized"] != "on":
        cmd.append("-r")
    if q["tissue"] != "all":
        cmd.extend(["-t", q["tissue"]])
    cmd.append(q["taxon_id"])

    download = "download" in q and q["download"] == "on"
    if download:
        response.headers["Content-Disposition"] = \
            'attachment; filename="matrix.tsv.gz"'
        p1 = Popen(cmd, stdout=PIPE)
        p = Popen(["pigz", "-9"], stdin=p1.stdout,
                stdout=PIPE)
        def g():
            while True:
                c = p.stdout.read(4096)
                yield c
                if len(c) < 4096:
                    break
        o = g()
    else:
        p = Popen(cmd, stdout=PIPE)
        o = p.stdout
    return o

application = api

if __name__ == "__main__":
    run(api, server="cherrypy", 
            host="0.0.0.0", port=7700)
