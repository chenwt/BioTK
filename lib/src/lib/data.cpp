#include <iostream>
#include <set>

#include "BioTK/data.hpp"
#include "BioTK/cache.hpp"
#include "BioTK/util.hpp"
#include "BioTK/ext/gzstream.hpp"

using namespace std;
using namespace BioTK;

namespace BioTK {
namespace data {
namespace NCBI {

string GENE_BASE_URL = 
    "ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/";
string GENE_INFO_URL = GENE_BASE_URL + "gene_info.gz";

shared_ptr<Gene>
gene(gene_id_t id) {
    static string 
        DB_PATH("~/.cache/BioTK/db/entrez_gene");
    static KVStore<gene_id_t,Gene> store(DB_PATH);

    if (store.empty()) {
        DownloadCache cache;
        set<size_t> seen;
        string line;
        path_t path = cache.fetch_path(GENE_INFO_URL);
        BioTK::ext::igzstream stream(path.c_str());

        getline(stream, line);
        while (getline(stream, line)) {
            vector<string> fields = split(line);
            Gene g = {
                (size_t) atol(fields[1].c_str()),
                (size_t) atol(fields[0].c_str()),
                0, 0};
            if (seen.find(g.id) != seen.end())
                continue;
            strncpy(g.symbol, fields[2].c_str(), 256);
            strncpy(g.name, fields[11].c_str(), 256);
            seen.insert(g.id);
            size_t g_id = g.id;
            store.put(g_id, g);
        }
    }
    return store.get(id);
};

};
};
};
