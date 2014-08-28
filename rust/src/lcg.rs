#![crate_name = "lcg"]
#![crate_type = "lib"]
#![feature(globs)]

extern crate core;
extern crate collections;

pub use statistics::*;

use core::clone;
use std::{from_str, f32};
use std::io::{BufferedReader};
use std::io;
use std::gc::{GC,Gc};
use collections::treemap::TreeMap;

pub mod statistics;

pub struct SeriesIndex {
    pub key : String,
    pub names : Vec<String>,
    pub lookup : TreeMap<String, uint>
}

impl core::clone::Clone for SeriesIndex {
    fn clone(&self) -> SeriesIndex {
        SeriesIndex{
            key:self.key.clone(), 
            names:self.names.clone(),
            lookup:self.lookup.clone()}
    }
}

impl SeriesIndex {
    pub fn new(key: String, names: Vec<String>) -> SeriesIndex {
        let mut lookup = TreeMap::new();
        for i in range(0, names.len()) {
            lookup.insert(names[i].clone(), i);
        }
        SeriesIndex{key:key, names:names, lookup:lookup}
    }

    pub fn to_delimited(& self, delimiter: char) -> () {
        print!("{}", self.key);
        for x in self.names.iter() {
            print!("{}{}", delimiter, x);
        }
        print!("\n");
    }

    pub fn to_tsv(& self) -> () {
        self.to_delimited('\t');
    }
}

pub struct Series {
    pub index : Gc<SeriesIndex>,
    valid : Vec<bool>,
    pub key : String,
    pub data : Vec<f32>
}

impl Series {
    //pub fn new(key : String, index: SeriesIndex, data : Vec<f32>) -> Series {
    pub fn new(key : String, index: Gc<SeriesIndex>, 
               data : Vec<f32>) -> Series {
        Series{key:key, 
            index:index,
            data:data.clone(),
            valid: data.iter().map(|x| x.is_nan().not()).collect()}
    }

    /* Private methods */

    fn copy_key(& self) -> String {
        String::from_str(self.key.as_slice())
    }

    /* Generic methods */

    pub fn map(& self, f: |&f32| -> f32) -> Series {
        Series::new(self.copy_key(), 
                    self.index,
                    self.data.iter().map(f).collect())
    }

    pub fn fold(& self, start: f32, f: |f32,&f32| -> f32) -> f32 {
        self.data.iter().filter(|x| x.is_nan().not()).fold(start, f)
    }

    /* Indexing */

    //pub fn iloc(& self, it: Iterator<uint>>) {
    //}

    /*
    pub fn dropna(& self) -> Series {
        let data : Vec<f32> = self.null.iter().zip(self.data.iter())
            .filter_map(|&n,&x| 
                        match n {
                            true => None,
                            false => Some(x)
                        }).collect();
        Series{key: String::from_str(self.key.as_slice()), data:data}
    }
    */

    /* Scalar methods */

    pub fn len(& self) -> uint {
        return self.data.len();
    }

    pub fn sum(& self) -> f32 {
        self.fold(0.0, |s,&x| s + x)
    }

    pub fn count_valid(& self) -> uint {
        self.valid.iter().filter(|&&x| x).count()
    }

    pub fn mean(& self) -> f32 {
        self.sum() / self.count_valid() as f32
    }

    pub fn var(& self) -> f32 {
        self.data.dropna().var()
    }

    pub fn std(& self) -> f32 {
        self.data.dropna().std()
    }

    pub fn max(& self) -> f32 {
        self.fold(f32::MIN_VALUE, |max,&x| 
                  if x > max { x } else { max })
    }

    pub fn min(& self) -> f32 {
        self.fold(f32::MAX_VALUE, |min,&x| 
                  if x < min { x } else { min })
    }

    pub fn range(& self) -> f32 {
        self.max() - self.min()
    }

    /* Methods returning another Series */

    pub fn standardize(& self) -> Series {
        let mu = self.mean();
        let stdev = self.std();
        self.map(|x| (x - mu) / stdev)
    }

    /* I/O methods */
    pub fn to_delimited(& self, delimiter: char) -> () {
        print!("{}", self.key);
        for &x in self.data.iter() {
            print!("{}{:.3f}", delimiter, x);
        }
        print!("\n");
    }

    pub fn to_tsv(& self) -> () {
        self.to_delimited('\t');
    }
}

/*
impl Add<Series, f32> for Series {
    fn add(&self, x: f32) {
    }
}
*/
pub struct SeriesReader<T> {
    pub index : Gc<SeriesIndex>,
    reader : BufferedReader<T>
}

impl <T : Reader> SeriesReader<T> {
    pub fn new(mut reader: BufferedReader<T>) 
            -> SeriesReader<T> {
        let ix = {
            let header : String = reader.read_line().unwrap();
            let mut fields = header.as_slice()
                .trim_right_chars('\n').split('\t');
            let ix_key = String::from_str(fields.next().unwrap());
            let ix_names : Vec<String> = fields
                .map(String::from_str).collect();
            box (GC) SeriesIndex::new(ix_key, ix_names)
        };
        SeriesReader{reader:reader, index: ix}
    }
}

impl <T : Reader> Iterator<Series> for SeriesReader<T> {
    fn next(&mut self) -> Option<Series> {
        match self.reader.read_line() {
            Ok(line) => {
                let mut fields = line.as_slice()
                    .trim_right_chars('\n').split('\t');
                let key = String::from_str(fields.next().unwrap());
                let data = fields.map(|x| 
                        from_str::<f32>(x).unwrap_or(f32::NAN)).collect();
                Some(Series::new(key, self.index, data))
            }
            Err(_) => None //Err("Failed to parse series.".to_string())
        }
    }
}
