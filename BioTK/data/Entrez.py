"""
Convenience functions to download and read commonly used Entrez datasets.
"""

import pandas as pd

from BioTK.io.NCBI import download

class Gene(object):
    @staticmethod
    def info(taxon_id):
        with download("/gene/DATA/gene_info.gz", compression="gzip") as handle:
            df = pd.read_table(handle,
                    skiprows=1,
                    names=["Taxon ID", "Gene ID", "Symbol", "Name"],
                    usecols=[0,1,10,11])
            df = df.ix[df["Taxon ID"] == taxon_id,:]
            df.drop_duplicates("Gene ID", inplace=True)
            df.index = df["Gene ID"]
            return df.drop("Gene ID", axis=1).drop("Taxon ID", axis=1)
