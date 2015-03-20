find_package(CUDA QUIET REQUIRED)
cmake_minimum_required(VERSION 3.1)

cuda_add_library(biotk_cuda
    dot.cu
    SHARED
)
