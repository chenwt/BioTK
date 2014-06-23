import datetime
import os
import subprocess as sp

from collections import namedtuple

Commit = namedtuple("Commit", "date,tags,message")

class Repository(object):
    def __init__(self, path=os.curdir):
        self.path = path

    @property
    def commits(self):
        o = sp.check_output(["git", "log", 
            "--format=format:%ad\t%s", "--date=iso", self.path])\
                    .decode("utf-8")
        fmt = "%Y-%m-%d %H:%M:%S %z"
        for line in o.strip().split("\n"):
            date, msg = line.split("\t")
            dt = datetime.datetime.strptime(date, fmt)
            tokens = msg.split(" ")
            tags = [t[1:] for t in tokens if t.startswith("!")]
            msg = " ".join([t for t in tokens if not t.startswith("!")])
            yield Commit(dt, tags, msg)
