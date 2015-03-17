#include <iostream>

#include <BioTK.hpp>

using namespace std;

int main() {
    string line;

    while (getline(cin, line)) {
        vector<string> v = BioTK::split(line);
        for (string& s : v) {
            double x = atof(s.c_str());
            cout.write(reinterpret_cast<const char*>(&x), sizeof x);
        }
    }
}
