#pragma once

#include <string>
#include <vector>

#include <htslib/sam.h>
#include <htslib/bgzf.h>

namespace BioTK {

struct Chromosome {
    std::string name;
    uint32_t length;
};

struct Read {
    const Chromosome* chromosome;
    int32_t start, end;
    uint32_t map_quality;
    std::string name;
    char strand; 
};

class BAMFile {
private:
    BGZF* file;
    bam_hdr_t* header;
    bam1_t* bam_read;
    bool eof = false;
    Read read;
    std::vector<Chromosome> chromosomes;

public:
    BAMFile(std::string path);
    ~BAMFile();

    Read* next();
};

}
