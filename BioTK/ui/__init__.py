import uuid

import numpy as np
import pandas as pd

from bottle import Bottle, static_file
from jinja2 import Environment, FileSystemLoader

from BioTK.db import get_session

root = Bottle()
env = Environment(loader=FileSystemLoader("resources/ui/templates"))
env.globals["db"] = db = get_session()
STATIC_ROOT = "resources/ui/static/"

def render_template(tmpl, **kwargs):
    if not "js_main" in kwargs:
        kwargs["js_main"] = "table"
    return env.get_template(tmpl).render(**kwargs)

class Table(object):
    """
    Tabular data to be rendered to HTML. This can either be a transient
    table, or a table that will be cached for later AJAX calls.
    """
    cache = {}

    def __init__(self, data, 
            title=None, link_format=None, link_columns=None,
            classes=None, server_side=False):
        self.data = data
        self.title = title
        self.link_format = link_format
        self.link_columns = link_columns
        self.classes = [] if classes is None else classes
        self.server_side = server_side

        if self.server_side:
            self.classes.append("data-table")
            self.uuid = str(uuid.uuid4())
            Table.cache[self.uuid] = self

    def render(self):
        return render_template("elements/table.html", table=self)

    def ajax(self, params):
        # FIXME: implement filtering, sorting
        start = int(params["start"])
        length = int(params["length"])
        order_column = int(params["order[0][column]"])
        order_ascending = params["order[0][dir]"] == "asc"
        search = params["search[value]"]

        def scalar(x):
            if isinstance(x, str):
                return x
            else:
                x = np.asscalar(x)
            if isinstance(x, float):
                return round(x, 2)
            return x

        if search:
            ix = np.zeros(self.data.shape[0], dtype=bool)
            for j in range(self.data.shape[1]):
                if self.data.dtypes[j] == object:
                    ix = np.logical_or(ix,
                            np.array(self.data.iloc[:,j]\
                                    .str.lower()\
                                    .str.contains(search.lower(), 
                                        regex=False),
                                    dtype=bool))
        else:
            ix = np.ones(self.data.shape[0], dtype=bool)
            
        if ix.sum() > 0:
            length = min(length, ix.sum()-start)
            rows = list(map(lambda row: tuple(map(scalar, row)), 
                self.data[ix]\
                        .sort(self.data.columns[order_column], 
                            ascending=order_ascending)\
                                    .iloc[start:(start+length),:]\
                                    .to_records(index=False)))
        else:
            rows = []

        return {
            "draw": int(params["draw"]),
            "recordsTotal": self.data.shape[0],
            "recordsFiltered": int(ix.sum()),
            "data": rows
        }

@root.route('/')
def index():
    return render_template('index.html')

@root.route("/favicon.ico")
def fn():
    return static_file("favicon.ico", root=STATIC_ROOT)

@root.route("/static/<path:path>")
def dispatch(path):
    return static_file(path, root=STATIC_ROOT)

# Sub-modules

from . import age
from . import region
