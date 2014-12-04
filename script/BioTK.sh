#!/usr/bin/env bash

# Basic sanity checks

[ "$(whoami)" == "root" ] && {
    echo "FATAL: BioTK cannot be run as root." 1>&2
    exit 1
}

export HOME="${HOME:=/home/$(whoami)}"
[ ! -d "$HOME" ] || [ ! -w "$HOME" ] && {
    echo "FATAL: \$HOME environment variable not set, directory doesn't exist, or user doesn't have write permissions. (\$HOME was detected as: '$HOME'" 1>&2
    exit 1
}

###############
# Configuration
###############

export XDG_DATA_HOME="${XDG_DATA_HOME:=$HOME/.local/share}"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:=$HOME/.config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:=$HOME/.cache}"

export BTK_DATA="${BTK_DATA:=$XDG_DATA_HOME/BioTK}"
export BTK_CACHE="${BTK_CACHE:=$XDG_CACHE_HOME/BioTK}"
export BTK_PREFIX="$HOME/.local/BioTK/prefix/"
mkdir -p "$BTK_DATA" "$BTK_CACHE" "$BTK_PREFIX/bin"

export PATH="$BTK_PREFIX/bin":"$PATH"
#export TMPDIR="$BTK_CACHE/tmp/"
#mkdir -p $TMPDIR

#######################
# External dependencies
#######################

#########
# Logging
#########

btk_log() {
    if which logger &> /dev/null; then
        logger -t BioTK -s "$@"
    else
        echo "*" "$@" 1>&2
    fi
}

###################
# Utility functions
###################

on_intranet() {
    host=wren.omrf.hsc.net.ou.edu
    test ! -z "$(dig +short $host)"
}
export -f on_intranet

tawk() {
    # awk, but with tabs as input/output delimiters

    awk -v FS='	' -v OFS='	' "$@"
}
export -f tawk

lzpaste() {
    # Like GNU 'paste', except for LZ4-compressed files.

    fifos=()
    tmpdir=$(mktemp -d)

    {
        for file in "$@"; do
            fifo=$(mktemp -p $tmpdir)
            rm $fifo
            mkfifo $fifo
            lz4 -dq $file > $fifo &
            fifos+=($fifo)
        done

        paste "${fifos[@]}"
    }

    rm -rf $tmpdir
}
export -f lzpaste

mkdir_cd() {
    mkdir -p "$1"
    cd "$1"
}

#########
# Caching
#########

_cache_download() {
    cache="$BTK_CACHE"/download
    mkdir -p "$cache"
    url="$1"
    name="$(echo "$url" | base64)"
    path="$cache/$name"
    if [ ! -f $path ]; then
        if which aria2c &> /dev/null; then
            aria2c -d "$cache" -o "$name" "$url"
        else
            curl -s -o "$path" "$url"
        fi
    fi &> /dev/null
    echo "$path"
}

cache_download() {
    path="$(_cache_download "$1")"
    cat "$path"
}
export -f cache_download

memoize() {
    # Given a function (name), and optionally arguments,
    # execute the function and cache the result as a file.
    cache="$BTK_CACHE/memoize"
    mkdir -p "$cache"
    path="$cache/$(echo "$@" | base64)"
    if [ ! -f "$path" ]; then
        "$@" | tee >(gzip > "$path")
    else
        zcat "$path"
    fi
}
export -f memoize

#############################
# Download essential datasets
#############################

btk_require_data() {
    # NCBI data
    ncbi_ftp=ftp://ftp.ncbi.nlm.nih.gov/
    _cache_download $ncbi_ftp/gene/DATA/gene_info.gz
}
export -f btk_require_data

#make -s -C "$BTK_DATA" -f "$(dirname $0)/BioTK.make" all
