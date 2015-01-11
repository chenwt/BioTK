using namespace std;

#include <iostream>

#include <BioTK/seq/sam.hpp>

using namespace BioTK;

int main(int argc, char* argv[]) {
    BAMFile bam(argv[1]);

    while (Read* read = bam.next()) {
        std::cout << read->chromosome->name
            << "\t" << read->start 
            << "\t" << read->end
            << "\t" << read->name
            << "\t" << read->map_quality
            << "\t" << read->strand
            << std::endl;
    }
}
