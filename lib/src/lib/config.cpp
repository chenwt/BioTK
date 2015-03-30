#include "BioTK/config.hpp"
#include "BioTK/util/fs.hpp"

using namespace std;

namespace BioTK {

typedef map<string, string> config_t;

void fix_paths(config_t& map) {
    for (auto& pair : map) {
        pair.second = expanduser(pair.second);
    }
}

const config_t DEFAULT_CONFIG = 
    {{"CACHE_ROOT", "~/.cache/BioTK"}};

const map<string,string>
get_configuration() {
    path_t path = expanduser("~/.BioTK.cfg");
    map<string,string> map = DEFAULT_CONFIG;

    if (path_exists(path)) {
        libconfig::Config cfg;
        cfg.readFile(path.c_str());
        for (auto& pair : map) {
            cfg.lookupValue(pair.first, pair.second);
        }
    }
    fix_paths(map);
    return map;
}

string 
config(string key) {
    auto cfg = get_configuration();
    return cfg[key];
}

};
