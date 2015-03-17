import bz2
import gzip
import mimetypes
import os
import tempfile
import base64
import urllib
import shutil
import subprocess

from urllib.parse import urlparse
from collections import OrderedDict

import numpy as np

from BioTK import LOG, CACHE_DIR

def as_float(x):
    try:
        return float(x)
    except ValueError:
        return np.nan

def generic_open(path, mode="rt"):
    """
    Open a file path, bzip2- or gzip-compressed file path,
    or URL in the specified mode.

    Not all path types support all modes. For example, a URL is not
    considered to be writable.

    :param path: Path
    :type path: str
    :throws IOError: If the file cannot be opened in the given mode
    :throws FileNotFoundError: If the file cannot be found
    :rtype: :py:class:`io.IOBase` or :py:class:`io.TextIOBase`,
      depending on the mode
    """

    # FIXME: detect zipped file based on magic number, not extension

    if hasattr(path, "read") or hasattr(path, "write"):
        return path

    parse = urlparse(path)
    type, compression = mimetypes.guess_type(path)

    if parse.scheme in ("http", "https", "ftp"):
        return download(path)

    if compression == "gzip":
        h = gzip.open(path, mode=mode)
    elif compression == "bzip2":
        h = bz2.BZ2File(path, mode=mode)
    else:
        h = open(path, mode=mode)
    return h

gopen = generic_open

class DelimitedFile(object):
    def __init__(self, path_or_handle, delimiter=","):
        self.handle = generic_open(path_or_handle)
        self.reader = csv.reader(self.handle, delimiter=delimiter)

    def __iter__(self):
        columns = next(self.reader)
        for fields in self.reader:
            yield OrderedDict(zip(columns, fields))

    def __enter__(self, *args, **kwargs):
        pass

    def __del__(self):
        self.handle.close()

    def __exit__(self, *args, **kwargs):
        self.handle.close()

class TSVFile(DelimitedFile):
    DELIMITER = "\t"

    def __init__(self, *args, **kwargs):
        kwargs["delimiter"] = self.DELIMITER
        super(DelimitedFile,self).__init__(*args, **kwargs)

def _download(url, unzip=None):
    # FIXME: download into temporary file and copy when done 
    # so cancelled downloads don't pollute the cache
    assert unzip in (None, "gzip")
    suffix = ""
    if unzip is not None:
        suffix = "-decompressed-" + unzip

    dest = os.path.join(CACHE_DIR.encode("utf-8"), 
            base64.b64encode((url+suffix).encode("utf-8"))).decode("utf-8")
    
    if not os.path.exists(dest):
        LOG.info("Download cache miss for URL: %s" % url)
        urllib.request.urlretrieve(url, dest)

        if unzip is not None:
            assert unzip=="gzip"
            t = tempfile.NamedTemporaryFile("w")
            subprocess.call("gzip -cd %s > %s" % (dest, t.name), shell=True)
            shutil.move(t.name, dest)
    else:
        LOG.info("Download cache hit for URL: %s" % url)
    return dest

def download(url, unzip=None, cache=True, open=True):
    assert cache, "Disabling download cache not implemented"
    path = _download(url, unzip=unzip)

    if open:
        return generic_open(path)
    else:
        return path

def read_set(handle):
    o = set()
    for line in handle:
        o.add(line.rstrip("\n"))
    return o
