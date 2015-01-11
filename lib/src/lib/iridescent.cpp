#include <algorithm>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <BioTK.hpp>
#include <BioTK/iridescent.hpp>

using namespace std;

namespace BioTK {

void make_binary_index(std::string ipath, std::string opath) {
    // Read a file full of unsigned 32-bit integers, one per line,
    // from a text file and output them, sorted, into a binary file at opath

    std::ifstream input(ipath);
    vector<uint32_t> v;
    string line;
    while (getline(input, line)) {
        v.push_back(atoi(line.c_str()));
    }
    sort(v.begin(), v.end());
    size_t map_size = sizeof(uint32_t) * v.size();

    int fd = open(opath.c_str(), O_RDWR | O_CREAT | O_TRUNC, (mode_t)0600);
    lseek(fd, map_size-1, SEEK_SET);
    write(fd, "", 1);
    uint32_t* map = (uint32_t*) mmap(0, map_size,
            PROT_READ | PROT_WRITE, MAP_PRIVATE, fd, 0);
    for (int i=0; i<v.size(); i++) {
        map[i] = v[i];
    }
    munmap(map, map_size);
    close(fd);
}

};
