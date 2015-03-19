#include <BioTK.hpp>

using namespace std;
using namespace BioTK;

void usage(int rc = 0) {
    cerr << "USAGE: knn [-k <int>] < input.tsv\n";
}

int main(int argc, char* argv[]) {
    size_t k = 5;
    bool show_usage = false;

    int c;
    while ((c = getopt(argc, argv, "k:h")) != -1) {
        switch (c) {
            case 'k':
                k = atol(optarg);
                break;
            case 'h':
                show_usage = true;
                break;
        }
    }

    SeriesReader reader;
    size_t nc = reader.p_index->labels.size();
    CoverTree tree(euclidean_distance, sqrt(nc), 1.2);
    Series* row;
    size_t i = 0;
    map<size_t, string> id_map;

    while (row = reader.next()) {
        /*
        double sd = arma::stddev(row->data);
        if (sd == 0)
            continue;
        double mean = arma::mean(row->data);
        arma::vec data = (row->data - mean) / sd;
        */
        id_map[i] = row->key;
        tree.add(i, row->data);
        i++;
    }

    cerr << "* cover tree built" << endl;
    size_t nr = id_map.size();
    cerr << CALL_COUNT << " " << (pow(nr, 2) / 2.0) - (nr / 2.0) << " " << pow(nr,2) << endl;
    CALL_COUNT = 0;

    for (auto pair : id_map) {
        vector<size_t> knn = tree.k_nearest(pair.first, k+1);
        cout << pair.second;
        for (size_t id : knn) {
            if (id != pair.first)
                cout << "\t" << id_map[id];
        }
        cout << endl;
    }

    cerr << CALL_COUNT << " " << (pow(nr, 2) / 2.0) - (nr / 2.0) << " " << pow(nr,2) << endl;
}
