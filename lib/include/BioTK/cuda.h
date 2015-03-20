#pragma once

// Number of 32-bit elements in a vector
#define CUDA_BLOCK_SIZE 512 

double biotk_cuda_dot(const double*, const double*);
