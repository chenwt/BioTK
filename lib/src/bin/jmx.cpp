#include <iostream>
#include <cstdio>
#include <unistd.h>
#include <signal.h>

#include <BioTK.hpp>

using namespace std;

void bwrite(ofstream& handle, double x) {
    handle.write(reinterpret_cast<const char*>(&x), sizeof x);
}

char tpath[1000];

void cleanup(int _) {
    unlink(tpath);
}

int main(int argc, char* argv[]) {
    char* path = argv[1];

    tmpnam(tpath);
    signal(SIGINT, cleanup);
    ofstream h(tpath, ios::out | ios::binary);

    BioTK::SeriesReader reader;
    vector<string> columns = reader.p_index->labels;
    double nc = columns.size();
    vector<string> index;

    while (BioTK::Series* s = reader.next()) {
        index.push_back(s->key);
        for (double x : s->data) {
            bwrite(h, x);
        }
    }
    h.close();
    double nr = index.size();

    size_t max_string_size = 0;
    for (string& c : columns) {
        max_string_size = max(max_string_size, c.size());
    }
    for (string& ix : index) {
        max_string_size = max(max_string_size, ix.size());
    }
    max_string_size = ceil((1 + max_string_size) / 8.0) * 8;

    cerr << "max string size: " << max_string_size << endl;
    cerr << "rows: " << nr << endl;
    cerr << "columns: " << nc << endl;

    ofstream out(path, ios::out | ios::binary);
    bwrite(out, (double) max_string_size);
    bwrite(out, nr);
    bwrite(out, nc);

    char buffer[max_string_size+1];
    for (string& ix : index) {
        memset(buffer, '\0', max_string_size+1);
        snprintf(buffer, max_string_size+1, ix.c_str());
        out.write(buffer, max_string_size);
    }
    for (string& c : columns) {
        memset(buffer, '\0', max_string_size);
        snprintf(buffer, max_string_size+1, c.c_str());
        out.write(buffer, max_string_size);
    }

    ifstream data(tpath, ios::in | ios::binary);
    out << data.rdbuf();

    //char cmd[1000];
    //sprintf(cmd, "cat %s > %s", tpath, path);
    //cout << tpath << endl;
    //sprintf(cmd, "du %s", tpath);
    //system(cmd);
    unlink(tpath);
}
