#!/usr/bin/env bash

pkgs=(
    realpath
    parallel
    tokyocabinet-bin libtokyocabinet-dev 
    pixz pigz
    liblz4-tool
    python3-numpy python3-scipy python3-matplotlib
)

sudo apt-get install -y ${pkgs[@]}
