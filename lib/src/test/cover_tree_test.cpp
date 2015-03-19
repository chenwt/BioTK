#include <armadillo>

#include <BioTK.hpp>

using namespace std;
using namespace BioTK;

int main() {
    CoverTree tree(correlation_distance, 1);

    arma::vec v1("1 2 3 4 5");
    arma::vec v2("5 4 3 2 1");
    arma::vec v3("1 2 1 2 1");
    arma::vec v4("5 4 3 1 2");
    tree.add(1, v1);
    tree.add(2, v2);
    tree.add(3, v3);
    tree.add(4, v4);

    vector<size_t> nearest = tree.k_nearest(1, 4);
    size_t expected[4] = {1,3,4,2};

    for (int i=0; i<nearest.size(); i++) {
        if (nearest[i] != expected[i]) {
            cerr << "FAIL" << endl;
            exit(1);
        }
    }
    cerr << "OK" << endl;
}
