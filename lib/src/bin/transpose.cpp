#include <stdio.h>
#include <unistd.h>
#include <cassert>
#include <vector>
#include <string>
#include <iostream>
#include <fstream>
#include <utility>
#include <sys/resource.h>

#include <BioTK.hpp>

using namespace std;

template <typename T>
vector<vector<T> >
transpose(vector<vector<T> >& X) {
    size_t nc = -1;
    for (auto x : X) {
        if (nc != -1) {
            assert(x.size() == nc);
        }
        nc = x.size();
    }
    size_t nr = X.size();

    vector<vector<T> > Xt;
    for (int j=0; j<nc; j++) {
        Xt.push_back(vector<T>(nr));
        vector<T>& v = Xt[j];
        for (int i=0; i<nr; i++) {
            v[i] = X[i][j];
        }
    }
    return Xt;
};

FILE* handle(vector<string>& chunk) {
    vector<vector<string> > X;
    for (string line : chunk) {
        X.push_back(BioTK::split(line));
    }

    char pattern[] = "/tmp/BioTK.transpose.XXXXXX";
    int tmp = mkstemp(pattern);
    FILE* h = fdopen(tmp, "r+");
    vector<vector<string> > Xt = transpose(X);
    for (vector<string>& v : Xt) {
        fprintf(h, "%s", v[0].c_str());
        for (int i=1; i<v.size(); i++) {
            fputc('\t', h);
            fprintf(h, "%s", v[i].c_str());
        }
        fputc('\n', h);
    }
    rewind(h);
    X.clear();
    return h;
}

string file_path(int fd) {
    char target[10000];
    sprintf(target, "/proc/self/fd/%d", fd);
    char fname[10000];
    readlink(target, fname, 10000);
    return string(fname);
}

string file_path(FILE* file) {
    return file_path(fileno(file));
}

pair<size_t, vector<string>* >*
get_chunk(size_t chunk_size, size_t& chunk_index) {
    vector<string>* chunk = new vector<string>(chunk_size);
    int i = 0;
    while ((i < chunk_size) && getline(cin, (*chunk)[i])) {
        i++;
    }

    if (i == 0) {
        delete chunk;
        return NULL;
    }
    chunk_index++;
    chunk->resize(i);
    return new pair<size_t, vector<string>* >(chunk_index, chunk);
}

int main() {
    rlimit limit;
    getrlimit(RLIMIT_NOFILE, &limit);
    size_t max_open_files = limit.rlim_max;

    size_t chunk_size = 100;
    size_t chunk_index = -1;
    vector<FILE*> files;
    pair<size_t, vector<string>* >* p;

    #pragma omp parallel shared(files, chunk_index) firstprivate (p)
    {
        #pragma omp master
        while (p = get_chunk(chunk_size, chunk_index))
        #pragma omp task
        {
            size_t ix = p->first;
            vector<string>* chunk = p->second;
            FILE* h = handle(*chunk);
            #pragma omp critical
            {
                cerr << "Processing lines " 
                    << ix * chunk_size
                    << "-" << (ix+1)*chunk_size << endl;
                if (files.size() < (ix + 1)) {
                    files.resize(ix + 1);
                }
                files[ix] = h;
            }
            delete chunk;
            delete p;
        }
        #pragma omp taskwait
    }

    /*
    string cmd = "paste";
    for (FILE* file : files) {
        cmd.append(" ");
        cmd.append(file_path(file));
    }
    system(cmd.c_str());
    exit(0);
    */

    /*
    size_t line_no = 0;
    while (getline(cin, line)) {
        line_no++;
        X.push_back(BioTK::split(line));
        if (X.size() == chunk_size) {
            handle(X, files);
        }
    }
    if (X.size() > 0) {
        handle(X, files);
    }
    */

    vector<ifstream*> handles;
    for (FILE* h : files) {
        ifstream* stream = new ifstream(file_path(h));
        handles.push_back(stream);
    }

    string line;
    bool ok = true;
    while (ok) {
        for (int i=0; i<handles.size(); i++) {
            if (!(getline(*handles[i], line))) {
                ok = false;
                break;
            }
            if (i > 0) {
                cout << "\t";
            }
            cout << line;
        }
        if (ok) 
            cout << endl;
    }

    for (auto h : handles) {
        delete h;
    }

    for (FILE* file : files) {
        string fname = file_path(fileno(file));
        unlink(fname.c_str());
        fclose(file);
    }
}
