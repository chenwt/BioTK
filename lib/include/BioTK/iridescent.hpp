#pragma once

#include <BioTK.hpp>

namespace BioTK {

class IRIDESCENT {
private:
    std::string basedir;

public:
    IRIDESCENT(std::string basedir) :
        basedir(basedir) {};

    void initialize();
};

void make_binary_index(std::string, std::string);

};
