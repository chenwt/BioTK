import argparse
import sqlite3
import sys
from contextlib import closing

from BioTK.io.Aspera import Client

def main():
    p = argparse.ArgumentParser(description="Bulk download data for commonly-used platforms from GEO")
    p.add_argument("--outdir", "-o", default=".")
    p.add_argument("--count", "-n", 
        default=5,
        help="Download the largest <n> platforms per species.")
    p.add_argument("species_name", nargs="+")
    args = p.parse_args()

    # FIXME: don't copy to fixed path
    # FIXME: implement in io
    # FIXME: maybe add GEOmetadb itself as a 'data' module
    url = "http://gbnci.abcc.ncifcrf.gov/geo/GEOmetadb.sqlite.gz"
    path = "/tmp/GEOmetadb.sqlite"

    import os, shutil, gzip, urllib.request
    if not os.path.exists(path):
        in_file = gzip.open(urllib.request.urlopen(url), "rb")
        with open(path, "wb") as out:
            shutil.copyfileobj(in_file, out)

    # FIXME: use io, to fallback to non-aspera
    client = Client()

    with closing(sqlite3.connect(path)) as db:
        c = db.cursor()

        for species in args.species_name:
            dir = os.path.join(args.outdir, species.replace(" ", "_"))
            os.makedirs(dir, exist_ok=True)
            c.execute("""
                SELECT gpl, count(gpl) FROM gsm 
                WHERE organism_ch1=?
                GROUP BY gpl
                ORDER BY COUNT(gpl) desc
                LIMIT ?""", (species, args.count))
            for gpl, count in c:
                url = "/geo/platforms/GPL%snnn/%s/soft/%s_family.soft.gz" % \
                    (gpl[3:-3], gpl, gpl)
                out_path = os.path.join(dir, "%s.soft.gz" % gpl)
                if not os.path.exists(out_path):
                    print("* Downloading %s ..." % gpl)
                    with client.download(url) as handle:
                        with open(out_path, "wb") as out:
                            shutil.copyfileobj(handle, out)

if __name__ == "__main__":
    main()
