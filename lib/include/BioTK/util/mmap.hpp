#pragma once

#include <string>

namespace BioTK {

class MemoryMappedFile {
    int handle;
    off_t fileSize;
    void *data;
public:
    MemoryMappedFile(std::string path);
    ~MemoryMappedFile();
    void* operator[](size_t offset);
};

}
