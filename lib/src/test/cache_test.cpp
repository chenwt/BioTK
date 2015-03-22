#include <BioTK.hpp>

using namespace std;
using namespace BioTK;

int main() {
    DownloadCache cache;
    ifstream stream;
    url_t url("http://google.com/");
    cache.fetch(stream, url);
    string line;
    while (getline(stream, line)) {
        cout << line << endl;
    }
}
