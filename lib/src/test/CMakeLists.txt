set(TARGETS 
    cover_tree_test
    cuda_dot_test
    cache_test
    base64
    serialize
    twobit
)

foreach( bin ${TARGETS} )
    set(src "${bin}.cpp")
    add_executable( ${bin} ${src} )
    target_link_libraries( ${bin} biotk gtest)
    add_test(
        NAME "${bin}"
        COMMAND "${bin}"
    )
endforeach( bin ${TARGETS} )
