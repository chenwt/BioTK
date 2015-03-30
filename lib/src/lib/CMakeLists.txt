add_library(biotk SHARED 
    algorithm/cover_tree.cpp
    cache.cpp
    config.cpp
    cuda.cpp 
    data.cpp
    io.cpp
    iridescent.cpp
    matrix.cpp
    seq/bbi.cpp
    seq/sam.cpp
    seq/twobit.cpp
    text/AhoCorasick.cpp
    util.cpp
    util/base64.cpp
    util/fs.cpp
    util/mmap.cpp
    util/net.cpp
)

set_target_properties(biotk PROPERTIES VERSION 
    ${BioTK_VERSION_STRING})

target_link_libraries(biotk 
    biotk_ext
    biotk_cuda 
    z

    armadillo
    config++
    curl
    glog
    hts
    leveldb
    cfish lucy 
    ssl
)
