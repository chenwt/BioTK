#!/usr/bin/env bash

cd $(dirname $0)/..
python3 setup.py doc
rsync -rvzd build/sphinx/html/ 10.84.146.24:/srv/http/code/BioTK/
