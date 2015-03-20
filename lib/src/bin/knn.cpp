#include <iostream>
#include <algorithm>
#include <set>
#include <limits>

#include <armadillo>

#include <BioTK.hpp>

using namespace std;

const double DOUBLE_MIN = numeric_limits<double>::min();

typedef set<arma::uword> index_t;

arma::uvec intersect(index_t& a, index_t& b) {
    vector<arma::uword> common;
    set_intersection(a.begin(),a.end(),b.begin(),b.end(),
            std::back_inserter(common));
    return arma::conv_to<arma::uvec>::from(common);
}

arma::uvec
get_order_fast(BioTK::matrix& Xs, int j) {
    size_t nc = Xs.ncol();
    arma::vec r2(nc);
    arma::vec x = Xs.data.col(j);
    for (int jj=0; jj<nc; jj++)  { 
        r2[jj] = arma::dot(x, Xs.data.col(jj)) / (nc - 1);
    }
    return arma::sort_index(r2, "descend");
}

arma::uvec 
get_order_with_missing(
        BioTK::matrix& X, vector<index_t>& indexes, 
        size_t min_samples, int j) {
    arma::vec r2(X.ncol());
    arma::vec x = X.data.col(j);
    index_t& ix_x = indexes[j];

    for (int jj=0; jj<X.ncol(); jj++) {
        arma::vec y = X.data.col(jj);
        index_t& ix_y = indexes[jj];
        arma::uvec ix = intersect(ix_x, ix_y);
        if (ix.size() < min_samples)
            r2[jj] = DOUBLE_MIN;

        arma::vec xx (x.elem(ix));
        arma::vec yy (y.elem(ix));
        arma::vec rs = arma::cor(xx, yy);
        r2[jj] = rs[0];
    }

    arma::uvec order = arma::sort_index(r2, "descend");
    int end = order.size();
    for (int i=0; i<order.size(); i++) {
        if (r2[order[i]] < -1) {
            end = i - 1;
        }
    }
    end = max(end, 2);
    return order.head(end);
}

void usage(int rc = 1) {
    cerr << "USAGE: knn [options]\n\n"
        << "Options:\n"
        << "  -k <int> : output top 'k' nearest neighbors\n"
        << "  -i :       assume the matrix has no\n"
        << "             missing values (faster)\n"
        << "  -m <int> : minimum number of samples required\n"
        << "             to compute a correlation\n"
        << "  -h : show this help\n";
    exit(rc);
}

int main(int argc, char* argv[]) {
    size_t k = 50;
    size_t min_samples = 25;
    int c;
    bool show_usage = false;
    // TODO: currently a misnomer, doesn't impute, but
    // assumes matrix is complete so dot product can be used
    bool impute = false;

    while ((c = getopt(argc, argv, "ik:m:")) != -1) {
        switch (c) {
            case 'k':
                k = atoi(optarg);
                break;
            case 'h':
                show_usage = true;
                break;
            case 'i':
                impute = true;
                break;
            case 'm':
                min_samples = atoi(optarg);
                break;
        }
    }

    if (show_usage) {
        usage(0);
    }

    ifstream input("/dev/stdin");
    BioTK::matrix X = BioTK::read_matrix(input);
    if (impute)
        X = X.standardize();

    assert(k < (X.ncol() - 1));

    vector<index_t> indexes(X.ncol());
    if (!impute) {
        for (int j=0; j<X.ncol(); j++) {
            arma::uvec ix = arma::find_finite(X.data.col(j));
            for (arma::uword v : ix)
                indexes[j].insert(v);
        }
    } 

    #pragma omp parallel for shared(X, indexes, min_samples)
    for (int j=0; j<X.ncol(); j++) {
        arma::uvec order;

        if (impute) {
            order = get_order_fast(X, j);
        } else {
            if (indexes[j].size() < min_samples)
                continue;
            order = get_order_with_missing(X, indexes, 
                    min_samples, j);
            if (order.size() < (k + 1))
                continue;
        }

        #pragma omp critical
        {
            size_t n = 0;
            size_t i = 0;
            cout << X.columns[j];
            while (n < k) {
                i++;
                if (order[i-1] == j)
                    continue;
                cout << "\t" << X.columns[order[i-1]];
                n++;
            }
            cout << endl;
        }
    }
}
