#include <BioTK.hpp>

#include "db_cxx.h"
#include "dbstl_map.h"

using namespace std;
using namespace BioTK::data::NCBI;
using namespace BioTK;

string dir("/home/gilesc/tmp2/");
string name("foo.db");

void create() {
    KVStore<size_t, Gene> store(dir, name);
    
    LOG(INFO) << "db open";

    Gene g = {123, 456, "abc", "def"};
    store.put(123, g);
    LOG(INFO) << "put";

    Gene g2 = store.get(123);
    LOG(INFO) << g2.symbol;
}

void check() {
    KVStore<size_t, Gene> store(dir, name);
    Gene g2 = store.get(123);
    LOG(INFO) << g2.symbol;
}

int main() {
    create();
    check();
}
