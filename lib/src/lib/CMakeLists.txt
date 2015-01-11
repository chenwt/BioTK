add_library(biotk SHARED 
    text/AhoCorasick.cpp
    util.cpp
    io.cpp
    matrix.cpp
    iridescent.cpp
    util/mmap.cpp
    seq/bbi.cpp
    seq/sam.cpp
)
target_link_libraries(biotk armadillo z hts)
