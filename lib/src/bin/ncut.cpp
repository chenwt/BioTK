#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <map>
#include <vector>
#include <string>
#include <iostream>
#include <fstream>

#include <BioTK.hpp>

using namespace std;

void usage() {
    cerr << "USAGE: TODO" << endl;
    exit(1);
}

int main(int argc, char* argv[]) {
    int c;
    vector<int> ix;
    vector<string> fields;
    string fields_path;

    string header, line;
    map<string,int> n2i;

    while ((c=getopt(argc, argv, "IF:")) != -1) {
        switch (c) {
            case 'F':
                fields_path = string(optarg);
                break;
            case 'I':
                ix.push_back(0);
                break;
        }
    }

    if (!fields_path.empty()) {
        ifstream file(fields_path.c_str());
        while (getline(file, line)) {
            fields.push_back(line);
        }
    } else if (optind < argc) {
        for (int i=optind; i<argc; i++) {
            fields.push_back(string(argv[i]));
        }
    } else {
        usage();
    } 

    getline(cin, header);
    vector<string> columns = BioTK::split(header);
    for (int i=0; i<columns.size(); i++) {
        n2i[columns[i]] = i;
    } 
    for (string f : fields) {
        if (n2i.find(f) != n2i.end()) {
            ix.push_back(n2i[f]);
        }
    }

    cout << columns[ix[0]];
    for (int i=1; i<ix.size(); i++) {
        cout << "\t" << columns[ix[i]];
    }
    cout << endl;

    while (getline(cin, line)) {
        vector<string> items = BioTK::split(line);
        cout << items[ix[0]];
        for (int i=1; i<ix.size(); i++) {
            cout << "\t" << items[ix[i]];
        }
        cout << endl;
    }
}
