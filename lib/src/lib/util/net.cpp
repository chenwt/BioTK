#include <cstdio>

#include <curl/curl.h>

#include "BioTK/util/net.hpp"

namespace BioTK {

size_t 
download_write_data(void *ptr, size_t size, 
        size_t nmemb, FILE *stream) {
    size_t written = fwrite(ptr, size, nmemb, stream);
    return written;
}

void 
download(url_t url, path_t dest) {
    CURL *curl;
    FILE *fp;
    CURLcode res;
    curl = curl_easy_init();
    if (curl) {
        fp = fopen(dest.c_str(), "wb");
        curl_easy_setopt(curl, CURLOPT_URL, 
            url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, 
            download_write_data);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, fp);
        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);
        fclose(fp);
    }
}

};
