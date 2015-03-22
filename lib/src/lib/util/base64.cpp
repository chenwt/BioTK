#include <stdint.h>
#include <cassert>

#include <openssl/bio.h>
#include <openssl/evp.h>
#include <openssl/buffer.h> 

#include "BioTK/util/base64.hpp"

#include <iostream>
using std::string;
using std::cout;
using std::endl;

namespace BioTK {
namespace base64 {

size_t 
decode_length(const string& input) {
    size_t n = input.size();
    size_t padding = 0;
 
    if (input[n-1] == '=' && input[n-2] == '=')
        padding = 2;
    else if (input[n-1] == '=')
        padding = 1;
 
    return n*0.75 - padding;
}

string 
decode(string input) {
    BIO *bio, *b64;
 
    size_t o_len = decode_length(input);
    char o[o_len+1];
 
    bio = BIO_new_mem_buf((void*) input.c_str(), -1);
    b64 = BIO_new(BIO_f_base64());
    bio = BIO_push(b64, bio);
 
    BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL);
    int length = BIO_read(bio, o, input.size());
    assert(length == o_len);
    string result(o, o_len);
    BIO_free_all(bio);
    return result;
}

string
encode(string input) {
    BIO *bio, *b64;
    BUF_MEM *bufferPtr;
 
    b64 = BIO_new(BIO_f_base64());
    bio = BIO_new(BIO_s_mem());
    bio = BIO_push(b64, bio);
 
    BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL);
    BIO_write(bio, input.c_str(), input.size());
    BIO_flush(bio);
    BIO_get_mem_ptr(bio, &bufferPtr);
    BIO_set_close(bio, BIO_NOCLOSE);
    string o(bufferPtr->data, bufferPtr->length);

    BIO_free_all(bio);
    return o;
}

};
};
