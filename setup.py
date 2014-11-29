#!/usr/bin/env python3

import os
import re
import pkgutil
import shutil
import subprocess
import sys

from os import walk
from os.path import join, dirname, splitext

from setuptools import setup, find_packages, Extension, Command
from setuptools.command.test import test as TestCommand
from pip.req import parse_requirements

args = sys.argv[2:]
devnull = open(os.devnull, "w")

##################################
# Check environment / dependencies
##################################

# Change to package root directory
os.chdir(os.path.abspath(os.path.dirname(__file__)))

# Ensure Python 3.2+

import platform
from distutils.version import StrictVersion
assert StrictVersion(platform.python_version()) > StrictVersion("3.2.0")

# Check native dependencies

class DependencyNotFound(Exception):
    def __init__(self, *args, **kwargs):
        super(DependencyNotFound, self).__init__(*args, **kwargs)

from distutils.spawn import find_executable

def read_requirements(path):
    with open(path) as h:
        for line in h:
            line = line.strip()
            if line and not line.startswith("#"):
                exe, name = line.split("\t")
                yield exe, name

distro_map = {
        "Arch Linux": "archlinux",
        "Ubuntu": "ubuntu"
}

def find_distribution():
    path = "/etc/os-release"
    if not os.path.exists(path):
        return
    with open(path) as h:
        m = re.search('NAME="(.+?)"', h.read())
        if m is not None:
            return distro_map.get(m.group(1))

def install_binary_dependencies():
    print("""One or more required binary packages could not be found. Would you like the installer to attempt automatic installation? This requires superuser privileges. (y/n)""")
    if input().lower() == "y":
        distro = find_distribution()
        if distro is not None:
            script = "install/%s.sh" % distro
            subprocess.call(["bash", script])
            return
    print("Aborting.")

if not "doc" in sys.argv:
    print("* Checking binary dependencies ...")

    for exe, name in read_requirements("binary-requirements.txt"):
        ok = find_executable(exe)
        msg = '\t%s ("%s") ... %s' % (name, exe, "OK" if ok else "FAIL")
        print(msg)
        if not ok:
            install_binary_dependencies()
            break

################################
# setup.py commands/entry points
################################

cmdclass = {}

try:
    import sphinx.setup_command
    class BuildDoc(sphinx.setup_command.BuildDoc):
        def __init__(self, *args, **kwargs):
            # TODO: Do programmatically
            subprocess.call(["sphinx-apidoc", "-o", "build/sphinx", "."])
            super(BuildDoc, self).__init__(*args, **kwargs)
    cmdclass["doc"] = BuildDoc
except ImportError:
    if "doc" in sys.argv:
        raise SystemExit("Sphinx is required to build documentation.")

try:
    from Cython.Distutils import build_ext
    cmdclass["build_ext"] = build_ext
except ImportError:
    pass

class Test(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = args
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        raise SystemExit(errno)

cmdclass["test"] = Test

class Clean(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        base = os.path.abspath(os.path.dirname(__file__))
        dirs = ["BioTK.egg-info", "build", "dist"]
        exts = [".pyc",".so",".o",".pyo",".pyd",".c",".cpp"]

        for dir in dirs:
            path = os.path.join(base, dir)
            if os.path.exists(path):
                print("* recursively removing", path)
                shutil.rmtree(path)

        for root, dirs, files in os.walk(base):
            for f in files:
                if os.path.splitext(f)[-1] in exts:
                    path = os.path.join(root, f)
                    print("* removing", path)
                    os.unlink(path)

cmdclass["clean"] = Clean

###############################
# Find scripts and requirements
###############################

entry_points = {"console_scripts":
                [
                    #"mmat = BioTK.mmat:cli"
                ]}

requirements = [str(item.req) for item in
        parse_requirements("requirements.txt")]

#########################
# Set include directories
#########################

include_dirs = []
try:
    import numpy
    include_dirs.append(numpy.get_include())
except ImportError:
    pass

###################
# Extension modules
###################

pxd = [
    "BioTK/genome/types.pxd",
    "BioTK/genome/index.pxd",
    "BioTK/io/_BBI.pxd"
]

extensions = [
    Extension("BioTK.genome.types",
        sources=pxd + ["BioTK/genome/types.pyx"],
        language="c++"),
    Extension("BioTK.genome.index",
        sources=pxd + ["BioTK/genome/index.pyx"],
        language="c++"),
    Extension("BioTK.io._BBI",
        sources=pxd + ["BioTK/io/_BBI.pyx"],
        language="c++"),
    Extension("BioTK.text.types",
        sources=["BioTK/text/types.pyx"],
        language="c++"),
    Extension("BioTK.text.AhoCorasick",
        sources=["BioTK/text/AhoCorasick.pyx"],
        language="c++")
]

def pkgconfig(*packages, **kw):
    flag_map = {'-I': 'include_dirs',
                '-L': 'library_dirs',
                '-l': 'libraries'}
    try:
        args = ["pkg-config", "--libs", "--cflags"]
        args.extend(packages)
        out = subprocess\
                .check_output(args, stderr=devnull)\
                .decode(sys.getdefaultencoding())
    except subprocess.CalledProcessError:
        raise DependencyNotFound()

    kw = {}
    for token in out.split():
        kw.setdefault(flag_map.get(token[:2]), []).append(token[2:])
    return kw

###############################
# Dynamically determine version
###############################

git_dir = os.path.join(os.path.dirname(__file__), ".git")
if os.path.exists(git_dir):
    VERSION = subprocess.check_output(["git", "describe", "--tags"]).strip()\
            .decode("utf-8")
    version_py = os.path.join(os.path.dirname(__file__), "BioTK", "version.py")
    try:
        with open(version_py, "w") as handle:
            handle.write("""version = '%s'""" % VERSION)
    except PermissionError:
        pass
else:
    VERSION = "HEAD"

#############################
# Resolve resource file paths
#############################

data_files = []
for root, dirs, files in os.walk("resources"):
    data_files.append((root,
        [os.path.join(root, f) for f in files if f!=".gitignore"]))

#####################
# Package description
#####################

setup(
    name="BioTK",
    author="Cory Giles, Mikhail Dozmorov, Xiavan Roopnarinesingh, Michael Ripperger",
    author_email="mail@corygil.es",
    version=VERSION,
    description="Utilities for genome analysis, expression analysis, and text mining.",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Scientific/Engineering :: Bio-Informatics"
    ],
    license="AGPLv3+",

    scripts=[os.path.join("script",x) for x in os.listdir("script")],

    zip_safe=False,
    packages=find_packages(),
    include_dirs=include_dirs,
    data_files=data_files,
    tests_require=requirements + ["pytest"],
    extras_require={
        "doc": requirements,
    },
    install_requires=requirements,
    ext_modules=extensions,
    entry_points=entry_points,

    # setup.py entry points
    cmdclass=cmdclass
)
