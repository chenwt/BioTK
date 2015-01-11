#include <string>

#include <BioTK/seq/sam.hpp>

namespace BioTK {

using namespace std;

BAMFile::BAMFile(string path) {
    file = bgzf_open(path.c_str(), "r");
    header = bam_hdr_read(file);
    for (int i=0; i<header->n_targets; i++) {
        Chromosome c;
        c.name = string(header->target_name[i]);
        c.length = header->target_len[i];
        chromosomes.push_back(c);
    }
    bam_read = bam_init1();
}

BAMFile::~BAMFile() {
        bam_destroy1(bam_read);
    bam_hdr_destroy(header);
    bgzf_close(file);
}

Read*
BAMFile::next() {
    bool ok = true;

    if (eof)
        return NULL;
    if (!bam_read1(file, bam_read)) {
        eof = true;
        return NULL;
    } else {
        // Skip if not proper pair
        ok &= bam_read->core.flag & BAM_FPROPER_PAIR != 0;
        
        read.chromosome = &chromosomes[bam_read->core.tid];
        read.start = bam_read->core.pos;
        read.end = bam_endpos(bam_read);
        read.name = string(bam_get_qname(bam_read));
        if (bam_is_rev(bam_read)) {
            read.strand = '-';
        } else {
            read.strand = '+';
        }
    }
    if (ok)
        return &read;
    return next();
}

}
