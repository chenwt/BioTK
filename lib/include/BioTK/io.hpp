#pragma once

#include <iostream>
#include <string>
#include <fstream>
#include <memory>

#include <BioTK/series.hpp>

namespace BioTK {

class SeriesReader {
private:
    Series* current = NULL;
    std::ifstream input;

public:
    std::shared_ptr<Index> p_index;

    SeriesReader(std::string path="/dev/stdin");
    ~SeriesReader();

    Series* next();
};

}
