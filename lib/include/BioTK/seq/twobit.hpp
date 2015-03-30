#pragma once

#include "BioTK/common.hpp"
#include "BioTK/util/mmap.hpp"

namespace BioTK {

enum TwoBitBlockType {
    N = 0,
    MASK = 1
};

struct TwoBitBlock {
    TwoBitBlockType type;
    uint32_t start;
    uint32_t size;
};

struct TwoBitBase {
    uint8_t _value : 2;

    char value() {
        switch (_value) {
            case (0): 
                return 'T';
            case (1):
                return 'C';
            case (2):
                return 'A';
            case (3):
                return 'G';
        }
    }
};

struct TwoBitBaseByte {
    TwoBitBase bases[4];
} __attribute__((packed));

struct TwoBitRecord {
    std::vector<TwoBitBlock> blocks;
    uint32_t size;
    TwoBitBaseByte* sequence;

    char operator()(size_t) const;

    std::string operator()(size_t, size_t) const;
};

class TwoBitFile {
    static const uint32_t MAGIC_NUMBER = 0x1A412743;

    struct Header {
        uint32_t signature, version, count, reserved;
    } __attribute__((packed));

    MemoryMappedFile data;
    Header header;
    std::map<std::string, TwoBitRecord> index;

public:
    TwoBitFile(path_t path) : data(MemoryMappedFile(path)) {
        header = *(Header*) data[0];
        if (header.signature != MAGIC_NUMBER) {
            throw std::invalid_argument(
                    "Not a two-bit format file!");
        }

        size_t offset = sizeof(Header);
        for (size_t i=0; i<header.count; i++) {
            uint8_t name_size = *((uint8_t*) data[offset]);
            offset += 1;
            std::string name((const char*) data[offset], 
                    name_size);
            offset += name_size;
            size_t r_offset = *((uint32_t*) data[offset]);
            offset += 4;

            TwoBitRecord r;
            r.size = *((uint32_t*) data[r_offset]);
            r_offset += 4;

            uint32_t n_blocks = *((uint32_t*) data[r_offset]);
            r_offset += 4;
            uint32_t n_block_starts = 
                *((uint32_t*) data[r_offset]);
            r_offset += 4 * n_blocks;
            uint32_t n_block_sizes =
                *((uint32_t*) data[r_offset]);
            r_offset += 4 * n_blocks;

            uint32_t m_blocks = *((uint32_t*) data[r_offset]);
            r_offset += 4;
            uint32_t m_block_starts = 
                *((uint32_t*) data[r_offset]);
            r_offset += 4 * m_blocks;
            uint32_t m_block_sizes =
                *((uint32_t*) data[r_offset]);
            r_offset += 4 * m_blocks;

            r_offset += 4; //reserved

            r.sequence = (TwoBitBaseByte*) data[r_offset];
            index[name] = r;
        }
    }

    const TwoBitRecord& operator[](std::string name) {
        return index[name];
    }
};

};
