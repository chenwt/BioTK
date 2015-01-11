#include <iostream>

#include <BioTK.hpp>

using namespace std;

int main() { 
    BioTK::SeriesReader rdr("/dev/stdin");
    cout.precision(3);
    cout << "\tN\tSum\tMean\tSD\tMedian\tGini\n";
    while (BioTK::Series* s = rdr.next()) {
        cout << s->key 
            << "\t" << s->valid()
            << "\t" << s->sum()
            << "\t" << s->mean() 
            << "\t" << s->std()
            << "\t" << s->median()
            << "\t" << s->gini()
            << endl;
    }
}
