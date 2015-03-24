#pragma once

#include <string>
#include <vector>

namespace BioTK {

template <typename T>
inline
std::string
serialize(const T& e) {
    std::string s(sizeof(e), '\0');
    memcpy((void*) s.c_str(), (void*) &e, sizeof(e));
    return s;
}

template <typename T>
inline
std::string
serialize(const std::vector<T>& v) {
    std::string o;
    o += serialize(v.size());
    for (const T& e : v)
        o += serialize(e);
    return o;
}

template <>
inline
std::string
serialize<std::string>(const std::string& s) {
    return s;
}

template <typename T>
inline
void deserialize(const std::string& s, T& o) {
    memcpy((void*) &o, (void*) s.c_str(), sizeof(T));
}

template <typename T>
inline
void deserialize(const std::string& s, std::vector<T>& o) {
    size_t size;
    deserialize(s, size);
    o.resize(size);
    memcpy((void*) &o[0], (void*) (s.c_str()+sizeof(size_t)),
            sizeof(T)*size);
}

template <>
inline
void deserialize<std::string>(
        const std::string& s, std::string& o) {
    o = s;
}

};
