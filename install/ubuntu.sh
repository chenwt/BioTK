#!/usr/bin/env bash

pkgs=(
    realpath
    parallel
    tokyocabinet-bin libtokyocabinet-dev 
    pixz pigz
    liblz4-tool
    python3-numpy python3-scipy python3-matplotlib
    python3-pandas
)

sudo apt-get install -y ${pkgs[@]}

for pkg in $(cat $(dirname $0)/../requirements.txt); do
    sudo pip3 install $pkg
done
