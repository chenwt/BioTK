#include <BioTK.hpp>

using namespace BioTK;

int main(int argc, char* argv[]) {
    DownloadCache cache;

    std::ifstream file;
    cache.fetch(file, argv[1]);
    std::cout << file.rdbuf();
}
