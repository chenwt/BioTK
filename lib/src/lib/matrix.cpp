#include <iostream>
#include <cassert>

#include <BioTK/matrix.hpp>

using namespace std;

BioTK::matrix
BioTK::matrix::transpose() {
    return BioTK::matrix(columns, index,
            arma::trans(data));
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
            o << "\t" << data(i,j);
        }
        o << endl;
    }
}

BioTK::matrix 
BioTK::read_matrix(istream& input) {
    string line, key;
    vector<vector<double> > X;
    vector<string> index, columns, fields;

    getline(cin, line);
    fields = split(line);
    for (int i=1; i<fields.size(); i++) {
        columns.push_back(fields[i]);
    }

    while (getline(cin, line)) {
        vector<double> data;
        fields = split(line);
        index.push_back(fields[0]);
        for (int i=1; i<fields.size(); i++) {
            data.push_back(atof(fields[i].c_str())); 
        }
        assert(data.size() == columns.size());
        X.push_back(data);
    }

    size_t nr = index.size();
    size_t nc = columns.size();
    arma::mat data(nr, nc);
    for (int i=0; i<nr; i++)
        for (int j=0; j<nc; j++)
            data(i,j) = X[i][j];
    return BioTK::matrix(index, columns, data);
}

BioTK::matrix
BioTK::matrix::standardize() {
    arma::mat data_std(nrow(), ncol()); 
    for (int j=0; j<ncol(); j++) {
        arma::vec v = data.col(j);
        data_std.col(j) = (v - arma::mean(v)) / arma::stddev(v);
    }
    return BioTK::matrix(index, columns, data_std);
}
