#include <armadillo>

#include <math.h>

namespace BioTK {

inline double
correlation_to_metric(double cor) {
    // Works for Pearson, Spearman, and cosine similarity
    // http://arxiv.org/pdf/1208.3145.pdf
    
    // NB. there is also a metric that puts highly 
    // correlated AND anticorrelated things close together:
    // sqrt(1 - cor(x,y)^2)
    return cor >= 1 ? 0 : sqrt((1.0 - cor) / 2.0);
}

size_t CALL_COUNT = 0;

#include <iostream>

inline double 
correlation_distance_standardized(
        const arma::vec& v1, 
        const arma::vec& v2) {

    CALL_COUNT++;
    return correlation_to_metric(arma::dot(v1,v2) / (v1.size() - 1));
}

double 
correlation_distance(
        const arma::vec& v1, 
        const arma::vec& v2) {

    arma::vec c = arma::cor(v1,v2);
    double r2 = c[0];
    return correlation_to_metric(r2);
}

double
euclidean_distance(
        const arma::vec& v1,
        const arma::vec& v2) {
    CALL_COUNT++;
    return sqrt(arma::sum(arma::pow(v1 - v2, 2)));
}

};
