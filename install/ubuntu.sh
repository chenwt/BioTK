#!/usr/bin/env bash

pkgs=(
    realpath
    parallel
    tokyocabinet-bin libtokyocabinet-dev 
    pixz pigz
    liblz4-tool
    python3-pip
    python3-numpy python3-scipy python3-matplotlib
    python3-pandas python3-patsy python3-numexpr
    python3-psycopg2 
    cython3
)

sudo apt-get install -y ${pkgs[@]}

for pkg in $(cat $(dirname $0)/../requirements.txt \
    | grep -v '#' | grep -v '^$'); do
    sudo pip3 install $pkg
done
