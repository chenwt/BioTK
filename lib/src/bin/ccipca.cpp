#include <BioTK.hpp>

using namespace std;

int main(int argc, char* argv[]) {
    int k = 100;

    int c;
    while ((c = getopt(argc, argv, "d:")) != -1) {
        switch (c) {
            case 'd':
                k = atoi(optarg);
                break;
        }
    }

    BioTK::SeriesReader reader;

    double amnesic = 1.0;
    int n = 0;
    size_t nc = reader.p_index->labels.size();
    double w1, w2;

    arma::rowvec mu(nc, arma::fill::zeros);
    arma::mat V(k, nc, arma::fill::zeros);

    // FIXME: sort output by explained variance ratio?
    
    while (BioTK::Series* s = reader.next()) {
        cerr << n << endl;
        if (n < amnesic) {
            w1 = (n + 1.0) / (n + 2.0);
            w2 = 1.0 / (n + 2.0);
        } else {
            w1 = (2.0 + n - amnesic) / (n + 2.0);
            w2 = (1.0 + amnesic) / (n + 2.0);
        }
        arma::rowvec u = s->data.t();

        mu *= w1;
        mu += u * w2;
        u -= mu;

        for (int j=0; j<k; j++) {
            if (j < n) {
                arma::rowvec v = V.row(j);
                double norm = arma::norm(v,2);
                arma::rowvec nv = v / norm;
                v *= w1;
                v += w2 * arma::dot(u, v) * u / norm;
                V.row(j) = v;

                u -= ((u.t() * nv) * nv.t()).t();
            } else if (j == n) {
                V.row(j) = u;
            }
        }
        n++;
    }

    for (int j=0; j<nc; j++) {
        cout << mu[j];
        for (int i=0; i<k; i++) {
            cout << "\t" << V.at(i,j);
        }
        cout << endl;
    }
    /*
    cout << mu.at(0);
    for (int j=1; j<nc; j++) {
        cout << "\t" << mu.at(j);
    }
    cout << endl;
    for (int i=0; i<k; i++) {
        cout << V.at(i,0);
        for (int j=1; j<nc; j++) {
            cout << "\t" << V.at(i,j);
        }
        cout << endl;
    }
    */
}
