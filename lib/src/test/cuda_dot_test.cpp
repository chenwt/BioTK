#include <cstdlib>
#include <cassert>

#include <BioTK.hpp>

#define N 512

using namespace std;

void basic_test() {
    int size = N * sizeof( double ); 
    double* a = (double *)malloc( size );
    double* b = (double *)malloc( size );
    for (int i=0; i<N; i++) {
        a[i] = 1;
        b[i] = 1;
    }
    float o = biotk_cuda_dot(a, b);
    free( a ); 
    free( b ); 
    cerr << o << endl;
    assert(o == N);
}

void cpp_api_test() {
    arma::vec v1("1 1 1 1 1");
    arma::vec v2("1 1 1 1 1");
    double o = BioTK::dot(v1, v2);
    cerr << o << endl;
    assert(o == 5);
}

int main() {
    basic_test();
    cpp_api_test();
}
