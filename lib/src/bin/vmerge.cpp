#include <map>
#include <iostream>
#include <libgen.h>

#include <BioTK.hpp>

using namespace std;

void usage() {
    cerr << "USAGE: TODO\n";
    exit(1);
}

int main(int argc, char* argv[]) {
    string fill_value = "0";
    int c;
    while ((c = getopt(argc, argv, "f:")) != -1) {
        switch (c) {
            case 'f':
                fill_value = string(optarg);
                break;
            default:
                usage();
        }
    }

    vector<string> keys;
    vector<map<string, string> > maps;
    string line, value;
    set<string> index;

    for (int i=optind; i<argc; i++) {
        keys.push_back(basename(argv[i]));
        maps.push_back(map<string,string>());
        ifstream input(argv[i]);
        while (getline(input, line)) {
            vector<string> fields = BioTK::split(line);
            maps[i-1][fields[0]] = fields[1];
            index.insert(fields[0]);
        }
    }
    
    for (string k : keys) {
        cout << "\t" << k;
    }
    cout << endl;

    for (string ix : index) {
        cout << ix;
        for (map<string,string>& m : maps) {
            value = fill_value;
            if (m.find(ix) != m.end())
                value = m[ix];
            cout << "\t" << value; 
        }
        cout << endl;
    }
}
