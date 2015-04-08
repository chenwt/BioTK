#pragma once

#include <armadillo>

#include "BioTK/common.hpp"

namespace BioTK {
namespace expression {

struct DEList {
    arma::ivec id;
    arma::vec intensity, logFC, p, FDR;

    DEList(std::string);
};

};
};
