#include <math.h>

namespace BioTK {

inline double
correlation_to_metric(double cor) {
    // Works for Pearson, Spearman, and cosine similarity
    // http://arxiv.org/pdf/1208.3145.pdf
    
    // NB. there is also a metric that puts highly 
    // correlated AND anticorrelated things close together:
    // sqrt(1 - cor(x,y)^2)
    return sqrt((1.0 - cor) / 2.0);
}

};
