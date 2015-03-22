#include "BioTK/data.hpp"
#include "BioTK/cache.hpp"
#include "BioTK/util.hpp"
#include "BioTK/ext/gzstream.hpp"

#include <iostream>
#include <set>

using namespace std;
using namespace BioTK;

namespace BioTK {
namespace data {
namespace NCBI {

/*
string GENE_BASE_URL = 
    "ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/";
string GENE_INFO_URL = GENE_BASE_URL + "gene_info.gz";

void 
Gene::initialize() {
    KVStore store = BioTK::kvstore("entrez_gene_symbol");

    if (store.size() == 0) {
        DownloadCache cache;
        set<size_t> seen;
        string line;
        path_t path = cache.fetch_path(GENE_INFO_URL);
        BioTK::ext::igzstream stream(path.c_str());

        getline(stream, line);
        while (getline(stream, line)) {
            vector<string> fields = split(line);
            size_t id = atoi(fields[1].c_str());
            if (seen.find(id) != seen.end())
                continue;
            seen.insert(id);
            store.put(fields[1], fields[2]);
        }
    }
}

string
Gene::name(gene_id_t id) {
    initialize();
    KVStore store = BioTK::kvstore("entrez_gene_symbol");
    return store.get(to_string(id));
}
*/

};
};
};
