"""
RWANDA: a simple, declarative framework enabling 
    Rapid Web ApplicatioN Development for Analytics
"""

import jinja2
import bottle

import yaml

class Application(object):
    def __init__(config_path):
        with open(config_path) as h:
            cfg = yaml.load(h)
        self.name = cfg["name"]

ui = Application()
