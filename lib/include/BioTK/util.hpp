#pragma once

#include <vector>
#include <string>

#include "util/mmap.hpp"

namespace BioTK {

std::vector<std::string> split(const std::string &text, char sep='\t');

std::string lowercase(std::string);
std::string uppercase(std::string);

}

