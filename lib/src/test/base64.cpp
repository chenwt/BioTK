#include <BioTK.hpp>

#include <gtest/gtest.h>

using namespace std;

const string decoded("abcdefgh");
const string encoded("YWJjZGVmZ2g=");

TEST(Base64Test, encode) {
    EXPECT_EQ(encoded, BioTK::base64::encode(decoded));
}

TEST(Base64Test, decode) {
    EXPECT_EQ(decoded, BioTK::base64::decode(encoded));
}

int main(int argc, char* argv[]) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
