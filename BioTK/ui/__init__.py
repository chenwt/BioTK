import os
import shutil
import functools
import itertools
from subprocess import Popen

import jinja2
import redis
import numpy as np
import pandas as pd

import bottle
from bottle import Bottle, static_file, debug, \
    jinja2_view as view, jinja2_template as template, \
    request, redirect
from jinja2 import Environment, FileSystemLoader

from BioTK import CONFIG, LOG
from BioTK.db import connect
from BioTK.git import Repository

TEMPLATE_ROOT = "resources/ui/templates"

cache = redis.StrictRedis(host="localhost", db=2)

repo = Repository()

root = Bottle()
debug(True)
env = Environment(loader=jinja2.FileSystemLoader([TEMPLATE_ROOT]))

def include_css(path):
    return """<link rel="stylesheet" href="/static/%s.css" />""" % path

def include_js(path):
    return """<script type="text/javascript" language="javascript" src="/static/%(path)s.js"></script>""" % locals()

db = connect()
env.globals.update({
    "db": db,
    "css": include_css,
    "js": include_js})

##############
# Static files
##############

STATIC_ROOT = "bower/components"
Popen(["bower", "install"], cwd="bower")

@root.route("/favicon.ico")
def fn():
    return static_file("BioTK/favicon.ico", root=STATIC_ROOT)

@root.route("/static/<path:path>")
def dispatch(path):
    return static_file(path, root=STATIC_ROOT)
