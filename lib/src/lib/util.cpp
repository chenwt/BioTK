#include "BioTK/common.hpp"

using namespace std;

namespace BioTK {

vector<string> 
split(const string &text, char sep) {
    vector<string> tokens;
    int start = 0, end = 0;
    while ((end = text.find(sep, start)) != string::npos) {
        tokens.push_back(text.substr(start, end - start));
        start = end + 1;
    }
    tokens.push_back(text.substr(start));
    return tokens;
}

string lowercase(string s) {
    std::transform(s.begin(), s.end(), s.begin(), ::tolower);
    return s;
}

string uppercase(string s) {
    std::transform(s.begin(), s.end(), s.begin(), ::toupper);
    return s;
}

bool startswith(const string& s, const string& q) {
    if (q.size() > s.size())
        return false;
    for (size_t i=0; i<q.size(); i++) {
        if (s[i] != q[i])
            return false;
    }
    return true;
}

bool endswith(const string& s, const string& q) {
    if (q.size() > s.size())
        return false;
    for (size_t i=q.size()-1; i>=0; i--) {
        if (s[i] != q[i])
            return false;
    }
    return true;
}

}
