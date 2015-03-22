#pragma once

#include "BioTK/common.hpp"

#include "BioTK/util/base64.hpp"
#include "BioTK/util/fs.hpp"
#include "BioTK/util/net.hpp"
#include "BioTK/util/mmap.hpp"

namespace BioTK {

/* String */
std::vector<std::string> 
    split(const std::string &text, char sep='\t');

std::string lowercase(std::string);
std::string uppercase(std::string);
bool startswith(const std::string&, const std::string&);
bool endswith(const std::string&, const std::string&);

/* Set operations */

template <typename T>
std::set<T>
intersection(std::set<T>& x, std::set<T>& y) {
    std::set<T> o;
    std::set_intersection(
            x.begin(),x.end(),
            y.begin(),y.end(),
            std::inserter(o,o.begin()));
    return o;
}

template <typename T>
std::set<T>
union_(std::set<T>& x, std::set<T>& y) {
    std::set<T> o;
    std::set_union(
            x.begin(),x.end(),
            y.begin(),y.end(),
            std::inserter(o,o.begin()));
    return o;
}

template <typename T>
size_t
intersection_size(std::set<T>& x, std::set<T>& y) {
    if (x.size() > y.size())
        return intersection_size(y,x);
    size_t o = 0;
    for (auto& elem : x) {
        if (y.find(elem) != y.end())
            o++;
    }
    return o;
}

template <typename T>
size_t
union_size(std::set<T>& x, std::set<T>& y) {
    size_t isect = intersection_size(x,y);
    return x.size() + y.size() - 2 * isect;
}

}

