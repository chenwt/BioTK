import os
import shutil
from subprocess import Popen

class FileLookup(object):
    def __init__(self, dirs, return_handle=True):
        self.return_handle = return_handle
        self.dirs = dirs

    def lookup(self, path):
        for d in self.dirs:
            p = os.path.join(d, path)
            if os.path.exists(p):
                return p
        raise KeyError
    
    def __getitem__(self, path):
        return self.lookup(path)

    @staticmethod
    def from_bower_json(self, bower_json):
        lookup_dirs = []
        components_dir = os.path.join(cache_dir, "bower_components")
        for root, dirs, files in os.walk(components_dir):
            for d in dirs:
                if d == "dist":
                    lookup_dirs.append(os.path.join(root, d))
        return FileLookup(lookup_dirs)

class UI(object):
    def __init__(self, 
            template_root=None,
            static_root=None,
            bower_json=None):

        self.template_lookup = FileLookup(template_root)

        if bower_json is not None:
            self.static_lookup = FileLookup.from_bower_json(bower_json)
        else:
            self.static_lookup = FileLookup([])
        if static_root is not None:
            self.static_lookup.dirs.append(static_root)

    def __call__(self, env, start_response):
        data = b"hi world"
        start_response("200 OK", [
            ("Content-Type", "text/plain"),
            #("Content-Length", str(len(data) * 2))
        ])
        yield data
        yield data

    def route(self, route, template=None):
        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            result = fn(*args, **kwargs)

root = UI(static_root="resources/ui/static", 
          bower_json="resources/ui/bower.json")
