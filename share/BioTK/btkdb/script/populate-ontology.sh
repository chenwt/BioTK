#!/usr/bin/env bash

[ $# != 3 ] && {
    echo "USAGE: $0 <abbreviation> <name> <path>"
    exit 1
} 1>&2

export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_COLLATE=en_US.UTF-8

abbreviation="$1"
name="$2"
path="$3"

get() {

python3 <(cat <<EOF
import sys
from BioTK.io.OBO import parse

with open(sys.argv[1], "r") as h:
    o = parse(h)
    o.${1}\
        .apply(lambda xs: ["".join(c for c in str(e) if ord(c) < 127).strip() for e in xs])\
        .to_csv(sys.stdout, header=False, sep="\t")
EOF
) $path

}

echo "* Importing $abbreviation ($name) ..." 1>&2

echo -e "$abbreviation\t$name" \
    | btkdb import ontology accession name

id=$(btkdb export ontology id accession \
    | tawk -va="$abbreviation" '$2==a {print $1}')

# Import terms

echo -e "\t* Importing terms ..." 1>&2

get terms \
    | cut -f1-2 \
    | tawk -v id=$id '{print id,$0}' \
    | btkdb import term ontology_id accession name

echo -e "\t* Importing synonyms ..." 1>&2

get synonyms | cut -f2 | insert-kvs synonym

echo -e "\t* Importing term-synonym links ..." 1>&2

get synonyms \
    | substitute-kvs term 1 accession \
    | substitute-kvs synonym 2 \
    | sort -u \
    | btkdb import entity_synonym entity_id synonym_id

relations=$(mktemp)
trap 'rm -f $relations' EXIT

get relations \
    | cut -f2-4 \
    | substitute-kvs term 1 accession \
    | substitute-kvs term 2 accession > $relations

echo -e "\t* Importing predicates ..." 1>&2

cut -f3 $relations | insert-kvs predicate

echo -e "\t* Importing term-term relations ..." 1>&2

substitute-kvs predicate 3 < $relations \
    | btkdb import relation \
        subject_id object_id predicate_id
