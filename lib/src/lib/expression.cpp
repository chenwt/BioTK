#include "BioTK/expression.hpp"
#include "BioTK/util.hpp"
#include "BioTK/matrix.hpp"

using namespace std;
using namespace BioTK;

namespace BioTK {
namespace expression {

DEList::DEList(string path) {
    // FIXME: expects edgeR output format
    // should try to infer from column names?
    ifstream input(path.c_str());
    BioTK::matrix X = BioTK::read_matrix(input);
    size_t nr = X.nrow();
    cout << nr << endl;
    id = arma::ivec(nr);
    for (int i=0; i<nr; i++) {
        id[i] = atoi(X.index[i].c_str());
    }
    logFC = arma::vec(X.data.col(0));
    intensity = arma::vec(X.data.col(1));
    p = arma::vec(X.data.col(3));
    FDR = arma::vec(X.data.col(4));
}

};
};
