#include <vector>
#include <iostream>
#include <sstream>
#include <assert.h>

using namespace std;

void split(vector<string> &tokens, const string &text, char sep) {
    int start = 0, end = 0;
    while ((end = text.find(sep, start)) != string::npos) {
        tokens.push_back(text.substr(start, end - start));
        start = end + 1;
    }
    tokens.push_back(text.substr(start));
}

int main() {
    vector<vector<string> > X;
    string line, e;

    int i = 0;
    int nc;
    while (getline(std::cin, line)) {
        std::istringstream ss(line);
        vector<string> fields;
        split(fields, line, '\t');

        if (i == 0) {
            nc = fields.size();
            for (int j=0; j<nc; j++) {
                X.resize(nc);
            }
        }
        assert(nc == fields.size());
        for (int j=0; j<nc; j++) {
            X[j].push_back(fields[j]);
        }
        i++;
    }

    int nr = X[0].size();

    for (int j=0; j<nc; j++) {
        cout << X[j][0];
        for (int i=1; i<nr; i++) {
            cout << "\t" << X[j][i];
        }
        cout << endl;
    }
}
