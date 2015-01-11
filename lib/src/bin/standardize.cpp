#include <iostream>

#include <BioTK.hpp>

using namespace std;

int main() {
    cout.precision(3);

    BioTK::SeriesReader rdr("/dev/stdin");
    for (auto c : rdr.p_index->labels) {
        cout << "\t" << c;
    }
    cout << endl;

    while (BioTK::Series* s = rdr.next()) {
        BioTK::Series std = s->standardize();
        cout << std.key;
        for (double v : std.data) {
            cout << "\t" << v;
        }
        cout << endl;
    }
}
