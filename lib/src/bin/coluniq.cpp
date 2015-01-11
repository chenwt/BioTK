#include <set>

#include <BioTK.hpp>

using namespace std;

void usage() {
    cerr << "USAGE: coluniq [-k <int>] < input\n\n"
        "uniq on a single column\n\n"
        "Options:\n"
        "   -k <int> : the column to uniq on\n";
    exit(1);
}

int main(int argc, char* argv[]) {
    int c;
    int i = 0;
    set<string> keys;
    string line;
    string input_path = "/dev/stdin";

    while ((c=getopt(argc, argv, "hk:")) != -1) {
        switch (c) {
            case 'k':
                i = atoi(optarg) - 1;
                assert(i >= 0);
                break;
            case 'h':
                usage();
                break;
        }
    }
     
    if (optind == argc - 1) {
        input_path = string(argv[optind]);
    }

    ifstream input(input_path);
    while (getline(input, line)) {
        vector<string> fields = BioTK::split(line);
        string key = fields[i];
        if (keys.find(key) == keys.end()) {
            cout << line << endl;
        }
        keys.insert(key);
    }

}
