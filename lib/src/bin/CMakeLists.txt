set(TARGETS 
    # Generic utility
    ncut csv2tsv transpose-block
    splitby coluniq vmerge
    pivot unpivot
    tsv2bin
    sample

    # Text
    tmatch 
    iridescent

    # Statistics / math
    summarize standardize log-transform ccipca
    knn

    # Sequencing
    bamcov

    # J
    jmx

    # Needs fixing
    # pcor 
    # corrwith
    # Uses more memory and slower than parallel/awk version
    # transpose    
)

foreach( bin ${TARGETS} )
    set(src "${bin}.cpp")
    add_executable( ${bin} ${src} )
    target_link_libraries( ${bin} biotk )
endforeach( bin ${TARGETS} )
