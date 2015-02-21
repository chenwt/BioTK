set(TARGETS 
    # Generic utility
    ncut csv2tsv transpose-block
    splitby coluniq vmerge
    pivot unpivot

    # Text
    tmatch iridescent-build

    # Statistics / math
    pcor summarize standardize log-transform

    # Sequencing
    bamcov

    # Needs fixing
    # corrwith
    # Uses more memory and slower than parallel/awk version
    # transpose    
)

foreach( bin ${TARGETS} )
    set(src "${bin}.cpp")
    add_executable( ${bin} ${src} )
    target_link_libraries( ${bin} biotk )
endforeach( bin ${TARGETS} )
