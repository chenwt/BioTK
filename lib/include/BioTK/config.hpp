#pragma once

#include <string>
#include <map>

#include <libconfig.h++>

namespace BioTK {

const std::map<std::string, std::string>
get_configuration(); 

std::string config(std::string);

};
