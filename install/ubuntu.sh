#!/usr/bin/env bash

pkgs=(
    realpath
    parallel
    tokyocabinet-bin libtokyocabinet-dev 
    pixz pigz
    liblz4-tool
    cython3
)

sudo apt-get install -y ${pkgs[@]}
