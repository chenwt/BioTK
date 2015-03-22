#include <string>

#include <gtest/gtest.h>

#include <BioTK.hpp>

using namespace BioTK;

TEST(KVStoreTest, StringToString) {
    KVStore<std::string,std::string> store(
            "/home/gilesc/db", "test");
    store.put("K", "V");
    EXPECT_EQ("V", store["K"]);
}

int main(int argc, char* argv[]) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
