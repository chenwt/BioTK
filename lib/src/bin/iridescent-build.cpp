#include <BioTK.hpp>

using namespace std;

void usage() {
    cerr << "USAGE: iridescent <command> <args>" << endl;
    exit(0);
}

int main(int argc, char* argv[]) {
    string ipath = string(argv[1]);
    string opath = string(argv[2]);
    BioTK::make_binary_index(ipath, opath);
}
