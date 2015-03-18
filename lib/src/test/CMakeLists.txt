set(TARGETS 
    cover_tree_test
)

foreach( bin ${TARGETS} )
    set(src "${bin}.cpp")
    add_executable( ${bin} ${src} )
    target_link_libraries( ${bin} biotk )
endforeach( bin ${TARGETS} )
