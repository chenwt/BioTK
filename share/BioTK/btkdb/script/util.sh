#!/usr/bin/env bash

###################
# Utility functions
###################

insert-kvs() {
    table="$1"
    sort -u \
        | comm -23 - <(btkdb export $table value | sort) \
        | btkdb import $table value
}
export -f insert-kvs

substitute-kvs() {
    table="$1"
    column="$2"
    column_key="$3"
    column_value="$4"
    if [[ -z "$column_key" ]]; then
        column_key=value
    fi
    if [[ -z "$column_value" ]]; then
        column_value=id
    fi
    dm translate -c "$column" \
        <(btkdb export "$table" "$column_key" "$column_value" | sed 1d)
}
export -f substitute-kvs
