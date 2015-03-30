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
        arma::vec data = s->data / s->sum();
        cout << s->key;
        for (double v : data) {
            cout << "\t" << v;
        }
        cout << endl;
    }
}
