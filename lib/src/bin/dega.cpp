#include <BioTK.hpp>

using namespace BioTK;
using namespace std;

int 
main(int argc, char* argv[]) {
    string path(argv[1]);
    BioTK::expression::DEList list(path);
    cout << list.p << endl;
}
