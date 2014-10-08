#!/usr/bin/env bash

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
