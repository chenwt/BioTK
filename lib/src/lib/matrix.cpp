#include <iostream>
#include <cassert>

#include <BioTK/matrix.hpp>

using namespace std;

BioTK::matrix
BioTK::matrix::transpose() {
    BioTK::matrix t;
    t.columns = index;
    t.index = columns;
    for (int j=0; j<ncol(); j++) {
        t.data.push_back(vector<double>());
        for (int i=0; i<nrow(); i++) {
            t.data[j].push_back(data[i][j]);
        }
    }
    return t;
}

void
BioTK::matrix::print(ostream& o) {
    for (int j=0; j<ncol(); j++) {
        o << "\t" << columns[j];
    }
    o << endl;
    for (int i=0; i<nrow(); i++) {
        o << index[i];
        for (int j=0; j<ncol(); j++) {
            o << "\t" << data[i][j];
        }
        o << endl;
    }
}

BioTK::matrix 
BioTK::read_matrix(istream& input) {
    BioTK::matrix matrix;
    string line, key;
    vector<string> index, fields;

    getline(cin, line);
    fields = split(line);
    for (int i=1; i<fields.size(); i++) {
        matrix.columns.push_back(fields[i]);
    }

    while (getline(cin, line)) {
        vector<double> data;
        fields = split(line);
        index.push_back(fields[0]);
        for (int i=1; i<fields.size(); i++) {
            data.push_back(atof(fields[i].c_str())); 
        }
        assert(data.size() == matrix.columns.size());
        matrix.data.push_back(data);
    }

    matrix.index = index;
    return matrix;
}
