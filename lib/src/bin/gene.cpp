#include "db_cxx.h"
#include "dbstl_map.h"

#include <BioTK.hpp>

using namespace std;
using BioTK::data::NCBI::Gene;
using namespace BioTK;

int main(int argc, char* argv[]) {
    int c;
    size_t taxon_id;

    while ((c = getopt(argc, argv, "t:")) != -1) {
        switch (c) {
            case 't':
                taxon_id = atoi(optarg);
                break;
        }
    }

    string line;
    while (getline(cin, line)) {
        size_t gene_id = atoi(line.c_str());
        shared_ptr<Gene> g = entrez_gene(gene_id);
        if (g) {
            cout << g->id
                << "\t" << g->symbol 
                << "\t" << g->name 
                << endl;
        }
    }
}
