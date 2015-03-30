#include "db_cxx.h"
#include "dbstl_map.h"

#include <BioTK.hpp>

using namespace std;
using BioTK::data::NCBI::Gene;
using namespace BioTK;

void print_gene(const Gene& g) {
    cout << g.id
        << "\t" << g.symbol 
        << "\t" << g.name 
        << endl;
}

int main(int argc, char* argv[]) {
    int c;
    size_t taxon_id = 0;

    while ((c = getopt(argc, argv, "t:")) != -1) {
        switch (c) {
            case 't':
                taxon_id = atoi(optarg);
                break;
        }
    }
    
    if (taxon_id != 0) {
        string 
            DB_PATH("~/.cache/BioTK/db/entrez_gene");
        KVStore<gene_id_t,Gene> store(DB_PATH);
        for (auto it=store.iter(); !it.eof(); ++it) {
            Gene g = it.value();
            if (g.taxon_id == taxon_id)
                print_gene(g);
        }
    } else {
        string line;
        while (getline(cin, line)) {
            size_t gene_id = atoi(line.c_str());
            shared_ptr<Gene> g = entrez_gene(gene_id);
            if (g) {
                print_gene(*g);
            }
        }
    }
}
