#!/usr/bin/env bash

###############
# Configuration
###############

log() {
    local OPTIND
    tag=BioTK
    while getopts :t: opt; do
        case $opt in
            t) tag="$OPTARG" ;;
            *) opts+="-$opt $OPTARG" ;;
        esac
    done
    which logger 2> /dev/null && {
        logger "$@"
    }
}
export -f log

cfg() {
    # Locate the BioTK configuration file and query it for the given key

    paths=(
        BioTK.yml
        $HOME/.BioTK.yml
        $HOME/.config/BioTK/BioTK.yml
        /opt/BioTK/BioTK.yml
        /etc/BioTK/BioTK.yml
    )

    for path in ${paths[@]}; do
        if [ -f $path ]; then
            v="$(shyaml get-value "$1" < $path)"
            if [[ ! -z "$v" ]]; then
                echo "$v"
                exit 0
            fi
        fi
    done 

    # Try the defaults last because it takes time to load the Python interpreter
    v=$(shyaml get-value "$1" < \
        $(python -c \
            'import BioTK; print(BioTK.resource.path("cfg/default.yml"))'))
    if [[ ! -z "$v" ]]; then
        echo "$v"
    else 
        exit 1
    fi
}
export -f cfg

export DATA="$(eval echo $(cfg data.root))"
export CACHE="$(eval echo $(cfg cache.root))"
mkdir -p "$CACHE" "$DATA"

on_intranet() {
    host=wren.omrf.hsc.net.ou.edu
    test ! -z "$(dig +short $host)"
}
export -f on_intranet

###################
# Utility functions
###################

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

#########
# Caching
#########

cache_download() {
    cache="$CACHE"/download
    mkdir -p "$cache"
    url="$1"
    name="$(echo "$url" | base64)"
    path="$cache/$name"
    if [ ! -f $path ]; then
        if which aria2c &> /dev/null; then
            aria2c -d "$cache" -o "$name" "$url"
        else
            curl -o "$path" "$url"
        fi
    fi &> /dev/null
    cat "$path"
}
export -f cache_download

memoize() {
    # Given a function (name), and optionally arguments,
    # execute the function and cache the result as a file.
    cache="$CACHE/memoize"
    mkdir -p "$cache"
    path="$cache/$(echo "$@" | base64)"
    if [ ! -f "$path" ]; then
        "$@" | tee >(gzip > "$path")
    else
        zcat "$path"
    fi
}
export -f memoize
