#include <string>
#include <iostream>
#include <vector>
#include <unordered_map>
#include <fstream>
#include <sstream>
#include <utility>

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

using namespace std;

typedef unordered_map<string, string> index_t;

vector<string> 
split(const string &text, char sep='\t') {
    std::vector<std::string> tokens;
    int start = 0, end = 0;
    while ((end = text.find(sep, start)) != std::string::npos) {
        tokens.push_back(text.substr(start, end - start));
        start = end + 1;
    }
    tokens.push_back(text.substr(start));
    return tokens;
}

string
join(const vector<string>& v, const string& sep="\t") {
    if (!v.empty())
    {
        std::stringstream ss;
        auto it = v.cbegin();
        while (true)
        {
            ss << *it++;
            if (it != v.cend())
                ss << sep;
            else
                return ss.str();
        }       
    }
    return "";
}

index_t
index_lines(istream& input, size_t i) {
    index_t ix;
    string line;
    while (getline(input, line)) {
        vector<string> fields = split(line);
        string key = fields[i];
        fields.erase(fields.begin()+i);
        string value = join(fields);
        ix[key] = value;
    }
    return ix;
}

void usage(int rc = 1) {
    cerr << "usage: todo\n";
    exit(rc);
}

int main(int argc, char* argv[]) {
    /* 
     * Wishlist:
     *  - can (eventually) do more than 2 joins at a time (?)
     */
    int c;
    size_t k1 = 0;
    size_t k2 = 0;
    string p1("/dev/stdin");
    string p2("");
    bool switch_index = false;
    bool switch_output_order = false;

    while ((c = getopt(argc, argv, "1:2:i")) != -1) {
        switch (c) {
            case '1':
                k1 = atoi(optarg) - 1;
                break;
            case '2':
                k2 = atoi(optarg) - 1;
                break;
            case 'i':
                switch_index = true;
                break;
        }
    }
    
    if (optind == argc - 2) {
        p1 = string(argv[optind]);
        p2 = string(argv[optind+1]);
    } else if (optind == argc - 1) {
        p2 = string(argv[optind]);
    } else {
        usage(1);
    }

    size_t k_in, k_ix;
    ifstream s_ix, s_in;
    if (!switch_index) {
        k_in = k1;
        k_ix = k2;
        s_in.open(p1);
        s_ix.open(p2);
    } else {
        k_in = k2;
        k_ix = k1;
        s_in.open(p2);
        s_ix.open(p1);
    }

    index_t ix = index_lines(s_ix, k_ix);

    string line;
    while (getline(s_in, line)) {
        vector<string> fields = split(line);
        string key = fields[k_in];
        if (ix.find(key) == ix.end())
            continue;

        fields.erase(fields.begin()+k_in);
        string o_in = join(fields);
        string& o_ix = ix[key];

        cout << key << "\t";
        if (!switch_output_order) {
            cout << o_ix << o_in;
        } else {
            cout << o_in << o_ix;
        }
        cout << endl;
    }
}
