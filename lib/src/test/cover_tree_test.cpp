#include <armadillo>

#include <BioTK.hpp>

using namespace std;

double correlation_distance(const arma::vec& v1, const arma::vec& v2) {
    arma::vec c = arma::cor(v1,v2);
    double r2 = c[0];
    return BioTK::correlation_to_metric(r2);
}

int main() {
    BioTK::CoverTree tree(correlation_distance, 100);
    arma::vec v1("1 2 3 4 5");
    arma::vec v2("5 4 3 2 1");
    arma::vec v3("1 2 1 2 1");
    tree.insert(0, v1);
    tree.insert(1, v2);
    //tree.insert(2, v3);
    /*
    for (size_t id : tree.k_nearest(v1, 2)) {
        cout << id << endl;
    }
    */
}
