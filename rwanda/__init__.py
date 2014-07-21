"""
RWANDA: a simple, declarative framework enabling 
    Rapid Web ApplicatioN Development for Analytics

It specializes in quickly developing simple web applications
displaying interactive tables and plots.
"""

import functools
import os
import shutil
import subprocess

import psycopg2
import jinja2
import bottle
import yaml

def include_css(path):
    return """<link rel="stylesheet" href="/static/%s.css" />""" % path

def include_js(path):
    return """<script type="text/javascript" language="javascript" src="/static/%(path)s.js"></script>""" % locals()

loader = jinja2.FileSystemLoader([self.TEMPLATE_ROOT])
env = jinja2.Environment(loader=loader)
env.globals.update({
    "isinstance": isinstance,
    "str": str,
    "js": include_js,
    "css": include_css
})

# Bower

PKGDIR = os.path.dirname(__file__)

class Application(object):
    TEMPLATE_ROOT = os.path.join(PKGDIR, "templates")
    BOWER_ROOT = os.path.expanduser("~/.cache/rwanda/bower")
    STATIC_ROOT = os.path.join(BOWER_ROOT, "components")

    def __init__(self, config_path):
        self.root = bottle.Bottle()

        with open(config_path) as h:
            self.cfg = yaml.load(h)

        self.template = env.get_template("base.html")
        self._install_bower_packages()
        self._make_static_route()
        self._connect_to_database()
    
    def _connect_to_database(self):
        cfg = self.cfg["database"]
        self.db = psycopg2.connect(
                user=cfg["user"],
                host=cfg["host"],
                port=cfg["port"],
                dbname=cfg["name"])

    def _install_bower_packages(self):
        os.makedirs(self.BOWER_ROOT, exist_ok=True)

        for fname in [".bowerrc", "bower.json"]:
            src = os.path.join(PKGDIR, "bower", fname)
            target = os.path.join(self.BOWER_ROOT, fname)
            if not os.path.exists(target):
                os.symlink(src, target)
                    
        try:
            os.symlink(os.path.join(PKGDIR, "bower", "rwanda"),
                    os.path.join(self.STATIC_ROOT, "rwanda"))
        except FileExistsError:
            pass

        subprocess.Popen(["bower", "install"], cwd=self.BOWER_ROOT).wait()

    def _make_static_route(self):
        self.root.get("/static/<path:path>")(
                lambda path: 
                    bottle.static_file(path, root=self.STATIC_ROOT))

    def route(self, route, method="get"):
        method = method.lower()
        assert method in ("get", "post")
        route_fn = self.root.get if method == "get" else self.root.post
        def wrapper(fn):
            @functools.wraps(fn)
            def wrap(*args, **kwargs):
                elements = fn(*args, **kwargs) or []
                return self.template.render(app=self, elements=elements)
            return route_fn(route)(wrap)
        return wrapper

    def serve(self):
        bottle.run(self.root, 
                port=self.cfg["server"]["port"],
                host=self.cfg["server"]["host"])

ui = Application("rwanda.yml")

@ui.route("/")
def fn():
    return

ui.serve()
