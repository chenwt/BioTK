#include "BioTK/seq/twobit.hpp"

using namespace std;

namespace BioTK {

char
TwoBitRecord::operator()(size_t pos) const {
    TwoBitBaseByte& byte = sequence[pos / 4];
    size_t bpos = pos % 4;
    return byte.bases[bpos].value();
}

};
