import os
import functools
import collections

import jinja2

from .. import env, root, view as _view, TEMPLATE_ROOT

base = env.get_template("base.html")

def get_template(name):
    return env.get_template("element/%s.html" % name)

class Static(object):
    def __init__(self, template_path):
        self.template_path = template_path

    def render(self):
        self.template = get_template(self.template_path)
        return self.template.render()

def view(route, method="get", **defaults):
    assert method in ("get", "post")
    method_fn = root.get if method == "get" else root.post

    def wrapper(fn):
        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            o = fn(*args, **kwargs)
            if o is None:
                return None
            if not isinstance(o, collections.Iterable):
                o = [o]
            params = {"elements": o}
            params.update(defaults)
            return base.render(**params)
        return method_fn(route)(wrap)
    return wrapper

class Element(object):
    def __init__(self, title=""):
        self.title = title

    def render(self):
        title = "<h3>%s<h3>" % self.title if self.title else ""
        content = title + self._render()
        return """<div class="row">%s</div>""" % content

from .table import *
from .plot import *
