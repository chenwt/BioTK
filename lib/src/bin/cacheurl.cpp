#include <BioTK.hpp>

using namespace BioTK;
using namespace std;

int main(int argc, char* argv[]) {
    bool output_path = false;

    int c;
    while ((c = getopt(argc, argv, "p")) != -1) {
        switch (c) {
            case 'p':
                output_path = true;
                break;
        }
    }
    argv += optind - 1;
    path_t path = string(argv[1]);

    DownloadCache cache;

    if (output_path) {
        cout << cache.fetch_path(path) << endl;
    } else {
        std::ifstream file;
        cache.fetch(file, path);
        std::cout << file.rdbuf();
    }
}
