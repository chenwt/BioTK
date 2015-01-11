#include <string>
#include <cassert>
#include <vector>
#include <fstream>
#include <iostream>
#include <utility>

#include <armadillo>

#include <BioTK.hpp>

using namespace std;

int main(int argc, char* argv[]) {
    // FIXME: doesn't work with new Index as shared_ptr
    
    assert(argc==2);
    ifstream map_file(argv[1]);
    string line;

    vector<string> names;
    vector<double> values;
    while (getline(map_file, line)) {
        vector<string> fields = BioTK::split(line);
        names.push_back(fields[0]);
        values.push_back(atof(fields[1].c_str()));
    }

    BioTK::Index o_ix;
    o_ix.initialize(names);
    BioTK::Series o(argv[1], &o_ix, arma::vec(values));

    BioTK::SeriesReader rdr;
    while (BioTK::Series* s = rdr.next()) {
        double r2 = s->cor(o);
        cout << s->key << "\t" << r2 << endl;
    }
}
