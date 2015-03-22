#include <cstdlib>
#include <cassert>
#include <iostream>
#include <unistd.h>

using namespace std;

void usage(int rc = 0) {
    cerr << "USAGE: sample [-p <float> | -n <int> ]\n\n"
        << "Options:\n"
        << "  -p <float> : Sample lines with probability p\n"
        << "  -n <int>   : Select every n lines\n";
    exit(rc);
}

int main(int argc, char* argv[]) {
    int c;
    bool show_usage = false;

    double probability = -1;
    size_t n = 0;

    while ((c = getopt(argc, argv, "hp:n:")) != -1) {
        switch (c) {
            case 'p':
                probability = atof(optarg);
                break;
            case 'h':
                show_usage = true;
                break;
            case 'n':
                n = atoi(optarg);
                break;
        }
    }

    if (show_usage)
        usage(0);

    if (n == 0) {
        if (!((probability >= 0) && (probability <= 1))) {
            usage(1);
        }
    }

    string line;
    size_t i = 0;
    while (getline(cin, line)) {
        if (n > 0) {
            if (i % n == 0) {
                cout << line << endl;
            }
        } else {
            double r = ((1.0 * rand()) / RAND_MAX);
            if (r < probability) {
                cout << line << endl;
            }
        }
        ++i;
    }
}
