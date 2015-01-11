#pragma once

#include <string>
#include <vector>
#include <istream>
#include <iostream>

#include <BioTK/util.hpp>

namespace BioTK {

struct matrix {
    std::vector<std::string> columns;
    std::vector<std::string> index;
    std::vector<std::vector<double> > data;

    size_t ncol() { return columns.size(); }
    size_t nrow() { return index.size(); }

    matrix transpose();
    void print(std::ostream& o=std::cout);
};

matrix read_matrix(std::istream& input);

}
