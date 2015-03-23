#include <string>
#include <vector>

#include <gtest/gtest.h>

#include <BioTK.hpp>

using namespace BioTK;

TEST(KVStoreTest, StringToString) {
    KVStore<std::string,std::string> store(
            "/home/gilesc/db", "test");
    store.put("K", "V");
    EXPECT_EQ("V", store["K"]);
}

TEST(KVMultiStoreTest, StringToString) {
    KVMultiStore<std::string,std::string> store(
            "/home/gilesc/db", "test2");
    store.add("K", "V");
    store.add("K", "V2");
    std::vector<std::string> vs = store["K"];
    EXPECT_EQ("V", vs[0]);
    EXPECT_EQ("V2", vs[1]);
}


int main(int argc, char* argv[]) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
