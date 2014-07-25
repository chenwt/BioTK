import os
import base64
import urllib.request

from .memory import *

from .. import LOG, CACHE_DIR

def download(url):
    dest = os.path.join(CACHE_DIR.encode("utf-8"), 
            base64.b64encode(url.encode("utf-8"))).decode("utf-8")
    
    if not os.path.exists(dest):
        LOG.info("Download cache miss for URL: %s" % url)
        urllib.request.urlretrieve(url, dest)
    else:
        LOG.info("Download cache hit for URL: %s" % url)

    return dest
