#include <cmath>

#include <BioTK.hpp>

using namespace std;

int main(int argc, char* argv[]) {
    cout.precision(3);

    int c;
    bool conditional = false;
    double mean, max_mean;
    double multiplier = 1;
    while ((getopt(argc, argv, "m:b:")) != -1) {
        switch (c) {
            case 'm':
                conditional = true;
                max_mean = atof(optarg);
                break;
            case 'b':
                multiplier = 1 / log(atof(optarg));
                break;
        }
    }

    BioTK::SeriesReader reader;
    for (string c : reader.p_index->labels) {
        cout << "\t" << c;
    }
    cout << endl;

    while (BioTK::Series* s = reader.next()) {
        bool apply = (!(conditional && s->mean() > max_mean));
        cout << s->key;
        arma::vec data = s->data;
        if (s->min()) {
            data += s->min() + 1;
        }
        for (double v : data) {
            if (apply) {
                v = log(v) * multiplier;
            }
            cout << "\t" << v;
        }
        cout << endl;
    }
}
