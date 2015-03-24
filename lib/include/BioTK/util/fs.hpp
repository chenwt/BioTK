#pragma once

#include "BioTK/common.hpp"

namespace BioTK {

bool mkdir_p(path_t);
std::string expanduser(path_t);
bool path_exists(path_t);
void copy_file(path_t, path_t);
std::vector<path_t> listdir(path_t);

path_t progname();

};
