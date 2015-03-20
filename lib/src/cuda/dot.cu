#include "BioTK/cuda.h"

__global__ void biotk_cuda_dot_gpu( double *a, double *b, double *c) {
    __shared__ double temp[CUDA_BLOCK_SIZE];
    temp[threadIdx.x] = a[threadIdx.x] * b[threadIdx.x];

    __syncthreads();

    if( 0 == threadIdx.x ) {
        double sum = 0;
        for( int i = CUDA_BLOCK_SIZE-1; i >= 0; i-- ){
            sum += temp[i];
        }
        *c = sum;
    }
}

double biotk_cuda_dot(const double* a, const double* b) {
    int size = CUDA_BLOCK_SIZE * sizeof( double ); 

    double *dev_a, *dev_b, *dev_o; // device copies of a, b, c
    double *o = (double *)malloc( sizeof( double ) );

    cudaMalloc( (void**)&dev_a, size );
    cudaMalloc( (void**)&dev_b, size );
    cudaMalloc( (void**)&dev_o, sizeof( double ) );

    cudaMemcpy( dev_a, a, size, cudaMemcpyHostToDevice );
    cudaMemcpy( dev_b, b, size, cudaMemcpyHostToDevice );

    // launch dot() kernel with 1 block and N threads
    biotk_cuda_dot_gpu<<< 1, CUDA_BLOCK_SIZE >>>( dev_a, dev_b, dev_o);
    // copy device result back to host copy of c
    cudaMemcpy( o, dev_o, sizeof( double ), cudaMemcpyDeviceToHost );

    double result = *o;
    free( o );
    cudaFree( dev_a );
    cudaFree( dev_b );
    cudaFree( dev_o );
    return result;
}
