add_library(biotk SHARED 
    cuda.cpp 
    algorithm/cover_tree.cpp
    text/AhoCorasick.cpp
    util.cpp
    io.cpp
    matrix.cpp
    iridescent.cpp
    util/mmap.cpp
    seq/bbi.cpp
    seq/sam.cpp
)

set_target_properties(biotk PROPERTIES VERSION 
    ${BioTK_VERSION_STRING})
target_link_libraries(biotk 
    biotk_cuda armadillo z hts cfish lucy)
