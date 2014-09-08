#!/usr/bin/env bash

q() {
python3 <(cat <<EOF
import string
import sqlite3
db = sqlite3.connect("$BTK_DATA/bioconductor/GEOmetadb.sqlite")
c = db.cursor()
c.execute("$1")
for row in c:
    try:
        fields = []
        for e in row:
            if e is None:
                e = ""
            e = str(e)\
                .replace("\n", "; ")\
                .replace("\t", " ")\
                .replace("\r", "")\
                .replace("\\\\", "/")\
                .strip()
            e = "".join(c for c in e if c in string.printable)
            #if not e:
            #    e = "\\\\N"
            fields.append(e)
        print(*fields, sep="\t")
    except UnicodeDecodeError:
        pass
EOF)
}

echo -e "\t* Inserting platform ..." 1>&2
q "SELECT organism,gpl,title,manufacturer FROM gpl" \
    | substitute-kvs taxon 1 name id \
    | dm cuniq 2 \
    | btkdb import platform taxon_id accession name manufacturer

echo -e "\t* Inserting series ..." 1>&2
q "SELECT gse,title,summary,type,overall_design FROM gse" \
    | dm cuniq 1 \
    | btkdb import series accession name summary type design

echo -e "\t* Inserting sample ..." 1>&2
q "SELECT gpl,gsm,CAST(channel_count AS integer),title,\
    description,status,type,\
    hyb_protocol,data_processing,contact \
    FROM gsm \
    WHERE channel_count IS NOT NULL" \
    | substitute-kvs platform 1 accession id \
    | btkdb import sample platform_id accession channel_count title \
        description status type hybridization_protocol \
        data_processing contact

for i in $(seq 1 2); do
    echo -e "\t* Inserting channel $i ..." 1>&2
    q "SELECT $i,gsm || '-' || $i, \
            gsm,organism_ch$i,source_name_ch$i,characteristics_ch$i,\
            molecule_ch$i,label_ch$i,treatment_protocol_ch$i,\
            extract_protocol_ch$i,label_protocol_ch$i\
        FROM gsm \
        WHERE channel_count >= $i" \
        | substitute-kvs sample 3 accession id \
        | substitute-kvs taxon 4 name id \
        | btkdb import channel \
            channel accession \
            sample_id taxon_id source_name characteristics \
            molecule label treatment_protocol extract_protocol \
            label_protocol
done

echo -e "\t* Inserting sample-series links ..."
q "SELECT gsm,gse FROM gse_gsm" \
    | substitute-kvs sample 1 accession id \
    | substitute-kvs series 2 accession id \
    | btkdb import sample_series sample_id series_id
