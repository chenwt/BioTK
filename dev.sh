#!/usr/bin/env bash

# Helpful bash functions for development

cfg=BioTK.task.config

unload() {
    neotool cypher "MATCH (n:\`$1\`) OPTIONAL MATCH (n)-[r]-() DELETE n,r"
}

unload-relation() {
    neotool cypher "MATCH (n1:\`$1\`)-[r]-(n2:\`$2\`) DELETE r"
}

info() {
    celery --config=$cfg inspect active
}

load() {
    python /dev/stdin <<-EOF
from BioTK.task.graph import load
load.${1}.apply_async()
EOF
}

label() {
    python /dev/stdin <<-EOF
from BioTK.task.graph import label
label.${1}.apply_async()
EOF
}

count() {
    neotool cypher "MATCH (n:\`$1\`) RETURN COUNT(n)"
}

clear-jobs() {
    celery --config=$cfg purge -f
    celery --config=$cfg purge -f
    redis-cli flushall
    redis-cli flushall
}
