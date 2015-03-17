#pragma once

#include <string>
#include <vector>
#include <istream>
#include <iostream>
#include <armadillo>

#include <BioTK/util.hpp>

namespace BioTK {

class matrix {
public:
    std::vector<std::string> columns;
    std::vector<std::string> index;
    arma::mat data;

    size_t ncol() { return columns.size(); }
    size_t nrow() { return index.size(); }

    matrix transpose();
    void print(std::ostream& o=std::cout);
    matrix standardize();

    matrix(
            std::vector<std::string> index,
            std::vector<std::string> columns,
            arma::mat data) :
        index(index), columns(columns), data(data) {};
};

matrix read_matrix(std::istream& input);

}
