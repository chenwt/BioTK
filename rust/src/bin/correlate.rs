#![feature(globs)]

extern crate collections;
extern crate lcg;

use collections::treemap::TreeSet;

use lcg::*;

use std::os;
use std::io::{File, BufferedReader,stdin};
use std::path::Path;
use std::iter::FromIterator;

fn main() {
    let q = {
        let args = os::args();
        let file = File::open(&Path::new(args[1].clone()));
        let mut rdr = lcg::SeriesReader::new(BufferedReader::new(file));
        rdr.next().unwrap()
    };
    let mut sr = lcg::SeriesReader::new(stdin());
    let r_index = sr.index.clone();

    let q_items : TreeSet<&String> = 
        FromIterator::from_iter(q.index.names.iter());
    let r_items : TreeSet<&String> = 
        FromIterator::from_iter(r_index.names.iter());
    let items : Vec<&&String> = q_items.intersection(&r_items).collect();
    if items.len() <= 1 {
        fail!("No intersection b/t keys");
    }
    let q_ix : Vec<&uint> = items.iter()
        .map(|&&x| q.index.lookup.find(x).unwrap()).collect();
    let r_ix : Vec<&uint> = items.iter()
        .map(|&&x| r_index.lookup.find(x).unwrap()).collect();
    let q_data : Vec<f32> = q_ix.iter().map(|&&i| q.data[i]).collect();

    println!("ID\tr\tn");
    for row in sr {
        let r_data : Vec<f32> = r_ix.iter().map(|&&i| row.data[i]).collect();
        let cor = r_data.correlate(&q_data);
        print!("{}", row.key);
        print!("\t{}\t{}", cor.r, cor.n);
        print!("\n");
    }
}
