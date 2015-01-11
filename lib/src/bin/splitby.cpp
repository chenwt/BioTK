#include <map>
#include <fstream>
#include <string>
#include <iostream>
#include <sys/stat.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <BioTK.hpp>

using namespace std;
using namespace BioTK;

void usage() {
    cerr << 
        "USAGE: dt-split [options] < tsv\n\n"
        "Options:\n"
        "   -m <path> : path to a mapping file to convert IDs\n"
        "   -H : input has no header\n"
        "   -v : verbosely print progress on stderr\n"
        "   -k <int> : 1-indexed index of the key column (default 1)\n"
        "   -K : don't output the key along with the rest of the line\n"
        "   -h : show this help\n";
    exit(1);
}

int main(int argc, char* argv[]) {
    int c;
    bool has_header = true;
    bool verbose = false;
    bool output_key = true;
    char* map_path = NULL;
    int key_ix = 0;

    while ((c=getopt(argc,argv,"KvHhm:k:")) != -1) {
        switch (c) {
            case 'H':
                has_header = false;
                break;
            case 'h':
                usage();
                break;
            case 'm':
                map_path = optarg;
                break;
            case 'v':
                verbose = true;
                break;
            case 'K':
                output_key = false;
                break;
            case 'k':
                key_ix = atoi(optarg) - 1;
                break;
        }
    }

    if (optind != argc) {
        usage();
    }

    map<string,string> mapping;
    string line, header, key, group;

    if (map_path != NULL) {
        ifstream map_file(map_path);
        while (getline(map_file, line)) {
            vector<string> fields = split(line);
            mapping[fields[0]] = fields[1];
        }
    }

    int n = 0;
    vector<string> header_fields;
    if (has_header) {
        getline(cin, header);
        header_fields = BioTK::split(header);
        if (!output_key) {
            header_fields.erase(header_fields.begin() + key_ix);
        }
    }

    struct stat buffer;   
    while (getline(cin, line)) {
        if (verbose && n && (n % 100) == 0) {
            cerr << "Processing line: " << n << endl;
        }
        n++;
        vector<string> fields = BioTK::split(line);
        key = fields[key_ix];

        if (map_path != NULL) {
            if (mapping.find(key) != mapping.end()) {
                group = mapping[key];
            } else {
                continue;
            }
        } else {
            group = key;
        }

        bool exists = ((stat (group.c_str(), &buffer) == 0));
        ofstream o(group, ios_base::app);
        if (!exists) {
            if (has_header) {
                o << header_fields[0];
                for (int i=1; i<header_fields.size(); i++) {
                    o << "\t" << header_fields[i];
                }
                o << endl;
            }
        }
        if (!output_key) {
            fields.erase(fields.begin() + key_ix);
        }
        o << fields[0];
        for (int i=1; i<fields.size(); i++) {
            o << "\t"  << fields[i];
        }
        o << endl;
    }
}
