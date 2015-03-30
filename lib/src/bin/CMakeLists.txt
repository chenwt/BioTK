set(TARGETS 
    # Generic utility
    ncut csv2tsv
    splitby coluniq vmerge
    pivot unpivot
    tsv2bin
    sample
    cacheurl
    njoin

    # Text
    tmatch 
    iridescent

    # Statistics / math
    summarize standardize log-transform ccipca
    knn knn2
    rand
    scale

    # Sequencing
    bamcov

    # J
    jmx

    # Needs fixing
    # pcor 
    corrwith
    # Uses more memory and slower than parallel/awk version
    # transpose    

    # Data
    gene
)

foreach( bin ${TARGETS} )
    set(src "${bin}.cpp")
    add_executable( ${bin} ${src} )
    target_link_libraries( ${bin} biotk )
endforeach( bin ${TARGETS} )
