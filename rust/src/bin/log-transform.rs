extern crate lcg;

use std::io;

fn main() {
    let mut sr = lcg::SeriesReader::new(std::io::stdin());
    sr.index.to_tsv();
    for series in sr {
        if series.range() > 100.0 {
            let v : Vec<f32> = series.data
                .iter().map(|x| x.log2()).collect();
            let s = lcg::Series::new(series.key, series.index, v);
            s.to_tsv()
        } else {
            series.to_tsv()
        }
    }
}
