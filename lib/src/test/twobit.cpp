#include <BioTK.hpp>

using namespace BioTK;
using namespace std;

int main() {
    DownloadCache cache;
    path_t path = cache.fetch_path("http://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.2bit");
    TwoBitFile twobit(path);
    auto record = twobit["chr1"];
    for (int i=50000; i<50010; i++)
        cout << record(i);
    cout << endl;
}
