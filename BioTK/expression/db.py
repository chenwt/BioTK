"""
An API for storing and querying RNA expression data in a HDF5 'database'.
"""

# How to organize the data/class hierarchy?
#     taxon -> platform -> (experiment / platform subset?) -> sample

# Currently the setup is a little confusing because there
# is a Platform object which shouldn't be confused with
# a BioTK.io.GEO.GPL object.

# TODO: Check for existence before returning Taxon, Platform, etc.

import re
import gzip
import pickle
from itertools import groupby

import h5py
import pandas as pd
import numpy as np

import BioTK.util
from BioTK.io import GEO, NCBI, generic_open
from .preprocess import normalize as _normalize, impute as _impute, \
        collapse as _collapse

def _get_prefix(accession):
    return accession[:-3] + "nnn"

def unpickle_object(data):
    return pickle.loads(bytes(data))

def pickle_object(obj):
    return np.array(pickle.dumps(obj))

class Platform(object):
    """
    A container for all the expression samples performed on the
    same platform.
    """
    def __init__(self, group):
        self._group = group

    def expression(self, 
            samples=None, 
            raw=False,
            collapse=None, normalize=True, impute=False):
        """
        Return expression data for samples from this platform.

        Parameters
        ----------
        samples : iterable of strings, optional
            The GEO GSM accessions to return. If not provided,
            *all* samples from this platform will be returned.
            This can be memory-intensive for large platforms!
        raw : bool, optional
            Return the expression data exactly as it was in the 
            original SOFT files. Overrides collapse, normalize, 
            and impute.
        collapse : str, optional
            Collapse probes to another identifier (e.g., gene ID).
            Acceptable options are provided by any column from the 
            .feature_attributes() method of this class.
        normalize : bool, optional
            Quantile normalize the expression data. 
        impute : bool, optional
            Replace missing values with imputed values using
            the default imputation method.

        Returns
        -------
        A :class:`pandas.DataFrame` with columns as samples and
            rows as probe IDs (or probe attributes, if the 
            'collapse' argument was provided).

        Notes
        -----
        For users familiar with Bioconductor's ExpressionSet class, 
        this function returns the equivalent of the "exprs" for these
        expression datasets.
        """
        # TODO: Raise error if a wrong GSM is provided?

        F = self.feature_attributes(raw=True)

        if samples is None:
            samples = self.sample_attributes().index

        samples = list(samples)

        ix = self._sample_index()
        ix = sorted([ix[s] for s in samples])
        X = pd.DataFrame(self._group["expression"][ix,:],
                index=samples, columns=F.index).T
        X.index.name = "Feature"
        X.columns.name = "Sample"

        if not raw:
            # Attempt to infer whether experiment was already 
            # log2 transformed or not. Is this the best cutoff?
            ix = X.max() > 100
            X.ix[:,ix] = (1+X.ix[:,ix]-X.ix[:,ix].min().min()).apply(np.log2)

            if collapse:
                # FIXME: handle probes mappings with '//'
                # TODO: factor out collapsing to preprocess
                X = _collapse(X, F[collapse])
                if isinstance(X.index[0], str):
                    X = X.ix[[(" /// " not in x) for x in X.index],:]
            if normalize:
                X = _normalize(X)
            if impute:
                # Renormalizing here b/c imputation may have
                # thrown off the distribution
                X = _normalize(_impute(X, axis=0))

        return X

    def _sample_index(self):
        P = self.sample_attributes(raw=True).index
        return dict(list(map(reversed, enumerate(P))))

    def sample_attributes(self, raw=False):
        """
        Obtain metadata for each sample, such as tissue type, age, etc.

        Parameters
        ----------
        raw : bool, optional
            If True, return the sample attributes exactly as they were
            imported. For GEO SOFT files, this can be quite messy and large.

        Returns
        -------
        A :class:`pandas.DataFrame` containing one row for each sample.

        Notes
        -----
        For users familiar with Bioconductor's ExpressionSet class, 
        this function returns the equivalent of the "pData" for these
        expression datasets.
        """
        if raw:
            return unpickle_object(self._group["sample"].value)

        # TODO: figure out how to use pandas str.extract on this 
        P = self.sample_attributes(raw=True)
        c = P["characteristics_ch1"].fillna("")
        records = []
        age_re = re.compile(r"\b[Aa]ge(.+?)?:\s*(?P<age>\d+(\.\d+)?)")
        tissue_re = re.compile(r"[Tt]issue:\s*([A-Za-z ]+)")
        cancer_re = re.compile("tumor|cancer|sarcoma|glioma|leukem|mesothelioma|metastasis|carcinoma", re.IGNORECASE)
        for s in c:
            m = age_re.search(s)
            age = float(m.group("age")) if m and m.group("age") else float("nan")
            m = tissue_re.search(s)
            tissue = m.group(1) if m else None
            cancer = cancer_re.search(s) is not None
            records.append((age, tissue, cancer))
        return pd.DataFrame.from_records(records, index=P.index,
                columns=["Age","Tissue","Cancer"])

    def feature_attributes(self, raw=True):
        """
        Obtain metadata for each feature (typically, an array probeset), such
        as mapped Gene IDs and symbols, array position, etc.

        Parameters
        ----------
        raw : bool, optional
            If True, return the sample attributes exactly as they were
            imported. For GEO SOFT files, this can be quite messy and large.

        Returns
        -------
        A :class:`pandas.DataFrame` containing one row for each feature.

        Notes
        -----
        For users familiar with Bioconductor's ExpressionSet class, 
        this function returns the equivalent of the "fData" for these
        expression datasets.
        """
        if raw is not True:
            raise NotImplementedError("Processing feature attributes is currently not implemented.")
        return unpickle_object(self._group["feature"].value)

    def _add_samples(self, geo_platform, it):
        """
        Add samples to this platform from a GEO Family iterator.
        """
        probes = geo_platform.table.index

        def expression(gsm):
            return np.array([gsm.expression.get(ix, np.nan)
                for ix in probes])

        n = len(probes)
        dataset = self._group.create_dataset("expression",
                dtype='f8', chunks=(1, n), maxshape=(None, n),
                compression="lzf",
                shape=(1, n))
        samples = []
        accessions = []

        chunk_size = 50
        end = 0
        for i,chunk in enumerate(BioTK.util.chunks(it, chunk_size)):
            start = end
            end = start + len(chunk)
            dataset.resize((end+1,n))
            data = np.zeros((len(chunk), n), dtype='f8')
            for j,gsm in enumerate(chunk):
                print("\t*", gsm.accession)
                accessions.append(gsm.accession)
                samples.append(pd.Series(gsm.attributes))
                data[j,:] = expression(gsm)[np.newaxis,:]
            dataset[start:end,:] = data

        samples = pd.DataFrame.from_records(samples,
                index=accessions)
        self._group.create_dataset("sample",
                data=pickle_object(samples))

class Taxon(object):
    """
    A container for all the different platforms belonging to a single
    taxon.
    """
    def __init__(self, group):
        self._group = group
        self.taxon_id = int(group.name.lstrip("/"))

    def __getitem__(self, accession):
        return self.platform(accession)

    def platform(self, accession):
        group = self._group[accession]
        return Platform(group)

    def _add_platform(self, geo_platform):
        group = self._group.create_group(geo_platform.accession)
        group.create_dataset("feature", 
                data=pickle_object(geo_platform.table))
        return self.platform(geo_platform.accession)

class ExpressionDB(object):
    def __init__(self, path, mode="a"):
        self._path = path
        self._store = h5py.File(path, mode)

    def __del__(self):
        self.close()

    def close(self):
        self._store.close()

    def add_taxon(self, taxon_id):
        key = "/%s" % taxon_id
        group = self._store.create_group(key)
        return self.taxon(taxon_id)

    def taxon(self, taxon_id):
        key = "/%s" % taxon_id
        self._store.require_group(key)
        group = self._store[key]
        return Taxon(group)

    def __getitem__(self, taxon_id):
        return self.taxon(taxon_id)

    def add_platform(self, accession):
        # We're storing by taxon ID which inexplicably is not
        #   in the GEO .annot files ...
        # To implement this method would need a Species Name <-> Taxon ID
        #   lookup.

        #platform = GEO.GPL.fetch(accession)
        #self._add_platform(platform)
        raise NotImplementedError

    #def platform(self, accession):
    #    return self._store.get(uri)

    def __contains__(self, taxon_id):
        return str(taxon_id) in self._store

    def add_family(self, accession_or_path):
        if accession_or_path.startswith("GPL"):
            accession = accession_or_path
            url = "/geo/platforms/GPL%snnn/%s/soft/%s_family.soft.gz" % \
                    (accession[3:-3], accession, accession)
            handle = NCBI.download(url, decompress="gzip")
        else:
            path = accession_or_path
            handle = generic_open(path)

        with handle:
            it = GEO.Family._parse_single(handle)
            geo_platform = it.__next__()
            taxon_id = geo_platform.taxon_id
            if not geo_platform.taxon_id in self:
                taxon = self.add_taxon(taxon_id)
            else:
                taxon = self.taxon(taxon_id)
            platform = taxon._add_platform(geo_platform)
            platform._add_samples(geo_platform, it)
        return platform
