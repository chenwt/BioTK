import mimetypes
import gzip
import bz2
from urllib.parse import urlparse
from collections import OrderedDict

import BioTK.cache

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

    if hasattr(path, "read"):
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

def download(url):
    path = BioTK.cache.download(url)
    return generic_open(path)
