#include <BioTK.hpp>

using namespace BioTK;
using namespace std;

int main() {
    size_t n = 5;
    cout << serialize(n).size() << endl;
    std::vector<int> v = {1,2,3};
    cout << serialize(v).size() << endl;
}
