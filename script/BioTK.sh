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

ifdef() {
    if [ $(which $1 2> /dev/null) ]; then
        echo "$2"
    else
        echo "$3"
    fi
}

export FAST_COMPRESS_PROGRAM=$(ifdef lz4 lz4 "gzip -1")
export PIGZ_PROGRAM=$(ifdef pigz pigz gzip)

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

zpaste() {
    # Like GNU 'paste', except for LZ4-compressed files.

    fifos=()
    tmpdir=$(mktemp -d)

    {
        for file in "$@"; do
            fifo=$(mktemp -p $tmpdir)
            rm $fifo
            mkfifo $fifo
            $FAST_COMPRESS_PROGRAM -dq $file > $fifo &
            fifos+=($fifo)
        done

        paste "${fifos[@]}"
    }

    rm -rf $tmpdir
}
export -f zpaste

mkdir_cd() {
    mkdir -p "$1"
    cd "$1"
}

#########
# Caching
#########

cache_download() {
    dlcache "$@"
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
