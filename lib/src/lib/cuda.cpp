#include <vector>
#include <cassert>

#include <armadillo>

#include "BioTK/cuda.hpp"

using namespace std;

namespace BioTK {

double dot(const arma::vec& v1, const arma::vec& v2) {
    assert(v1.size() == v2.size());
    size_t n = v1.size();
    size_t n_blocks = ceil(1.0 * n / CUDA_BLOCK_SIZE);

    double o = 0;
    if (n % CUDA_BLOCK_SIZE == 0)
        n_blocks++;

    for (size_t blk=0; blk<n_blocks-1; blk++) {
        const double* vv1 = v1.memptr() + CUDA_BLOCK_SIZE * blk;
        const double* vv2 = v2.memptr() + CUDA_BLOCK_SIZE * blk;
        o += biotk_cuda_dot(vv1, vv2);
    }

    if (n % CUDA_BLOCK_SIZE != 0) {
        size_t start = CUDA_BLOCK_SIZE * (n_blocks - 1);
        size_t end = n - start;

        double vv1[CUDA_BLOCK_SIZE];
        double vv2[CUDA_BLOCK_SIZE];
        bzero(vv1, sizeof(double) * CUDA_BLOCK_SIZE);
        bzero(vv2, sizeof(double) * CUDA_BLOCK_SIZE);
        memcpy((void*) vv1, 
               (void*) (v1.memptr() + start),
               sizeof(double) * (end - start));
        memcpy((void*) vv2, 
               (void*) (v2.memptr() + start),
               sizeof(double) * (end - start));
        o += biotk_cuda_dot(vv1, vv2);
    }
    return o;
}

};
