#include "BioTK/common.hpp"

namespace BioTK {
namespace data {
namespace NCBI {

struct Gene {
    size_t id;
    size_t taxon_id;
    char symbol[256];
    char name[256];
} __attribute__((packed));

std::shared_ptr<Gene> gene(size_t id);

/*
struct GeneSet {
    std::string name, description;
    std::vector<gene_id_t> genes;
} __attribute__((packed));
*/

};
};

inline
std::shared_ptr<BioTK::data::NCBI::Gene>
entrez_gene(size_t id) {
    return BioTK::data::NCBI::gene(id);
}

};
