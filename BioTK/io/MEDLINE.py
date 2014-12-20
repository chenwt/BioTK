"""
Parser for MEDLINE XML files.

Example:

.. code-block:: python
   
    from BioTK.io import MEDLINE

    path = "http://www.nlm.nih.gov/databases/dtd/medsamp2013.xml.gz"
    with MEDLINE.parse(path) as h:
        for article in path:
            print(article)
"""

import datetime
import locale
import re
import os
import gzip
import pickle
import xml.etree.ElementTree as ET

from collections import namedtuple

from BioTK import mixin
from BioTK.io import generic_open
from BioTK import CONFIG, LOG

__all__ = ["parse", "Article", "Journal"]

Article = namedtuple("Article", 
                     "id title abstract publication_date journal")
Journal = namedtuple("Journal", "id issn name")

class MedlineXMLFile(mixin.Closing):
    # FIXME: Date parsing will probably only work if system
    #   locale is US English

    _months = dict((i, locale.nl_langinfo(getattr(locale, "ABMON_" + str(i))))
                        for i in range(1,13))
    _non_digit_regex = re.compile(r"[^\d]+")

    def __init__(self, path):
        self._handle = generic_open(path, "rb")
    
    def close(self):
        self._handle.close()
    
    def _text(self, xpath):
        try:
            return self._current_element.findall(xpath)[0].text
        except IndexError:
            return None

    def _strip_non_digit(self, text):
        return self._non_digit_regex.sub('', text)

    def _parse_citation(self):
        # Parse Article information
        pmid = int(self._text(".//PMID"))
        title = self._text(".//Article/ArticleTitle")
        abstract = self._text(".//Article/Abstract/AbstractText")

        publication_date = None
        year = self._text(".//Article/Journal/JournalIssue/PubDate/Year")
        if year:
            month = self._text(".//Article/Journal/JournalIssue/PubDate/Month")
            month = self._months.get(month, "01")
            day = self._text(".//Article/Journal/JournalIssue/PubDate/Day") or "01"
            publication_date = datetime.date(int(year), int(month), int(day))

        # Parse Journal information
        journal_id = self._text(".//MedlineJournalInfo/NlmUniqueID")
        journal_id = int(self._strip_non_digit(journal_id))
        journal_issn = self._text(".//MedlineJournalInfo/ISSNLinking")
        journal_name = self._text(".//MedlineJournalInfo/MedlineTA")
        journal = Journal(journal_id, journal_issn, journal_name)

        return Article(pmid, title, abstract, publication_date, journal)

    def __iter__(self):
        for event, element in ET.iterparse(self._handle):
            if event == "end" and element.tag == "MedlineCitation":
                self._current_element = element
                yield self._parse_citation()

def parse(path_or_handle, cache=True):
    if not cache:
        return MedlineXMLFile(path_or_handle)
    else:
        try:
            path = path_or_handle if isinstance(path_or_handle, str) \
                    else path_or_handle.name
            pkl_basename = os.path.basename(path).split(".")[0] + ".pkl.gz"
            pkl_path = os.path.join(CONFIG["ncbi.medline.dir"], pkl_basename)
            if not os.path.exists(pkl_path):
                LOG.info("[medline] Caching MEDLINE XML parse as %s" \
                        % pkl_basename)
                articles = list(MedlineXMLFile(path))
                with gzip.open(pkl_path, "wb") as h:
                    pickle.dump(articles, h)
        except Exception as e:
            with gzip.open(pkl_path, "wb") as h:
                pickle.dump([], h)
        try:
            with gzip.open(pkl_path) as h:
                articles = pickle.load(h)
        except Exception as e:
            articles = []
        return iter(articles)
