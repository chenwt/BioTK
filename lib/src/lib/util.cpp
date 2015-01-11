#include <algorithm>

#include <BioTK/util.hpp>

namespace BioTK {

std::vector<std::string> 
split(const std::string &text, char sep) {
    std::vector<std::string> tokens;
    int start = 0, end = 0;
    while ((end = text.find(sep, start)) != std::string::npos) {
        tokens.push_back(text.substr(start, end - start));
        start = end + 1;
    }
    tokens.push_back(text.substr(start));
    return tokens;
}

std::string lowercase(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), ::tolower);
    return s;
}

std::string uppercase(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), ::toupper);
    return s;
}

}
