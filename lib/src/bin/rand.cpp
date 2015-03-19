#include <random>
#include <unistd.h>
#include <iostream>
#include <cassert>
#include <functional>

using namespace std;

void usage(int rc = 1) {
    cerr << "USAGE: todo" << endl;
    exit(rc);
}

template <class RNG>
void rvector(RNG& rng, size_t nr) {
    for (size_t i=0; i<nr; i++) {
        cout << rng() << endl;
    }
}

template <class RNG>
void rmatrix(RNG& rng, size_t nr, size_t nc) {
    for (size_t j=0; j<nc; j++) {
        cout << "\tC" << (j+1);
    }
    cout << endl;

    for (size_t i=0; i<nr; i++) {
        cout << "R" << (i+1);
        for (size_t j=1; j<nc; j++) {
            cout << "\t" << rng();
        }
        cout << endl;
    }
}

int main(int argc, char* argv[]) {
    cout.precision(3);
    getopt(argc, argv, "");

    size_t nr = 10;
    size_t nc = 10;

    assert((argc - optind) <= 2);

    default_random_engine generator;
    uniform_real_distribution<double> distribution(0.0, 1.0);
    auto rng = bind(distribution, generator);

    switch (argc - optind) {
        case 0:
            rmatrix(rng, nr,nc);
            break;
        case 1:
            nr = atol(argv[argc - 1]);
            rvector(rng, nr);
            break;
        case 2:
            nr = atol(argv[argc - 2]);
            nc = atol(argv[argc - 1]);
            rmatrix(rng, nr,nc);
            break;
        default:
            usage(1);
            break;
    }
}
