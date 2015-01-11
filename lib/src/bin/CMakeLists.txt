set(TARGETS 
    # Generic utility
    ncut csv2tsv transpose transpose-block
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
)

foreach( bin ${TARGETS} )
    set(src "${bin}.cpp")
    add_executable( ${bin} ${src} )
    target_link_libraries( ${bin} biotk )
endforeach( bin ${TARGETS} )
