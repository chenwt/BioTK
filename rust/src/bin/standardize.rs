extern crate lcg;

use std::io;

fn main() {
    let mut sr = lcg::SeriesReader::new(std::io::stdin());
    sr.index.to_tsv();
    for series in sr {
        series.standardize().to_tsv();
    }
}
