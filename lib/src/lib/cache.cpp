#include "BioTK/cache.hpp"
#include "BioTK/util/base64.hpp"
#include "BioTK/util.hpp"
#include "BioTK/ext/gzstream.hpp"

using namespace std;
using namespace BioTK;

namespace BioTK {
namespace cache {

string
DownloadCache::fetch_path(url_t url) {
    string key = BioTK::base64::encode(lowercase(url));
    string path = dir + "/" + key;
    if (!path_exists(path)) {
        download(url, path);
    }
    return path;
}

void 
DownloadCache::fetch(ifstream& handle, url_t url) {
    path_t path = fetch_path(url);
    handle.open(path);
}
 
}; // ns cache

}; // ns BioTK
