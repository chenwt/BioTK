#![feature(globs)]

extern crate rustrt;
extern crate libc;
extern crate btk;
extern crate getopts;
extern crate collections;

use std::str::from_utf8;
use std::io::{IoError, FilePermission, BufferedReader, File, stdin};
use std::os::{MemoryMap,MapOffset,MapWritable,MapReadable,MapFd,args};
use std::collections::HashMap;
use rustrt::rtio::{Open, ReadWrite};
use std::path::{Path};
use std::vec::raw::{from_buf};
use std::vec::Vec;
use std::mem;
use collections::hash::Hash;

use btk::*;
use getopts::{optopt,reqopt,getopts};

unsafe fn open(path : Path) -> *mut libc::FILE {
    libc::fopen(path.to_c_str().as_ptr(), "rw".to_c_str().as_ptr())
}

pub static MagicNumber : u32 = 0x62630a67;

pub mod posix {
    extern crate libc;

    extern {
        pub fn posix_fallocate(fd: libc::c_int, offset: libc::off_t, 
            len: libc::off_t) -> libc::c_int;
        pub fn mmap(addr : *const libc::c_char, length : libc::size_t, 
                prot : libc::c_int,   flags  : libc::c_int, 
                fd   : libc::c_int,   offset : libc::off_t) -> *mut u8;
        pub fn munmap(addr : *mut u8, length : libc::size_t) -> libc::c_int;
    }

    /* prot values */
    pub static PROT_NONE   : libc::c_int = 0x0;
    pub static PROT_READ   : libc::c_int = 0x1;
    pub static PROT_WRITE  : libc::c_int = 0x2;
    pub static PROT_EXEC   : libc::c_int = 0x4;

    /* flags */
    pub static MAP_SHARED  : libc::c_int = 0x1;
    pub static MAP_PRIVATE : libc::c_int = 0x2;
}

/*
fn pack(x: String) -> Vec<u8> {
    msgpack::Encoder::to_msgpack(&x).ok().unwrap()
}

fn unpack(x: Vec<u8>) -> String {
    msgpack::from_msgpack(x).ok().unwrap()
}
*/

pub struct Matrix {
    base : Path,
    file : libc::c_int,
    data : *mut f32,
    size : u64,
    columns : Vec<String>,
    rows : Vec<String>
}

unsafe fn mmap(file : libc::c_int, size : u64) -> *mut u8 {
    posix::mmap(0 as *const libc::c_char, size,
            posix::PROT_WRITE, posix::MAP_SHARED, file, 0)
}

fn index_of<T: PartialEq>(v: Vec<T>, item: T) -> uint {
    for i in range(0, v.len()) {
        if v.get(i) == &item {
            return i;
        }
    }
    -1
}

fn positions<T: Eq + Hash>(xs: Vec<T>, ys: Vec<T>) -> Vec<Option<uint>> {
    let mut m : HashMap<&T, uint> = HashMap::new();
    let mut ixs : Vec<Option<uint>> = Vec::new();
    for i in range(0, xs.len()) {
        m.insert(xs.get(i), i);
    }
    for y in ys.iter() {
        ixs.push(
            match m.find(&y) {
                Some(ix) => Some(ix.clone()),
                None => None
            }
        );
    }
    ixs
}

fn positions_from_file(path: Path, xs: Vec<String>) -> Vec<uint> {
        let mut file = BufferedReader::new(File::open(&path));
        let names = file.lines().map(|x| x.unwrap()
            .as_slice().trim_right_chars('\n').to_string())
            .collect();
        positions(xs, names)
            .iter().filter_map(|&x| x).collect()
}

impl Matrix {
    unsafe fn open(path : Path) -> Result<Matrix, IoError> {
        if !path.exists() {
            std::io::fs::mkdir(&path, std::io::UserRWX);
        }
        unsafe {
            let data_path = path.join("data");
            let create = !data_path.is_file();
            let fd = libc::open(data_path.to_c_str().as_ptr(), 
                    libc::O_RDWR | libc::O_CREAT,
                    libc::S_IRUSR | libc::S_IWUSR);
            if create {
                posix::posix_fallocate(fd, 0, 1000000);
            }
            let sz = data_path.stat().unwrap().size;
            let columns : Vec<String> = Vec::new();
            let rows : Vec<String> = Vec::new();
            let mut m = 
                Matrix{base: path, file:fd, data: mmap(fd, sz) as *mut f32, 
                    size: sz, columns: columns, rows: rows};
            if create {
                m.write_indices();
            } else {
                m.read_indices();
            }
            Ok(m)
        }
    }

    fn read_index(&mut self, name: String) -> Vec<String> {
        let path = self.base.join(name);
        if path.is_file() {
            let mut file = BufferedReader::new(File::open(&path));
            file.lines().map(|x| x.unwrap().as_slice()
                .trim_right_chars('\n').to_string()).collect()
        } else {
            Vec::new()
        }
    }

    fn read_indices(&mut self) -> () {
        self.rows = self.read_index("rows".to_string());
        self.columns = self.read_index("columns".to_string());
    }

    fn write_rows(&self) {
        let path = self.base.join("rows");
        let mut file = File::create(&path);
        for row in self.rows.iter() {
            file.write_line(row.as_slice());
        }
    }

    fn write_columns(&self) {
        let path = self.base.join("columns");
        let mut file = File::create(&path);
        for column in self.columns.iter() {
            file.write_line(column.as_slice());
        }
    }
    
    fn write_indices(&self) {
        self.write_rows();
        self.write_columns();
    }

    fn set_columns(&mut self, columns: Vec<String>) {
        self.columns = columns.clone();
        self.write_columns();
    }

    unsafe fn append(&mut self, s: Series) {
        let offset = self.columns.len() * self.rows.len();
        self.rows.push(s.key.clone());
        let needed = offset + self.columns.len();
        self.reserve(needed);

        std::slice::raw::mut_buf_as_slice(
            self.data, offset + self.columns.len() as uint,
                |x : &mut [f32]| {
            for j in range(0, self.columns.len()) {
                x[offset+j] = s.data[j];
            }
        });
    }

    unsafe fn irow(&self, i: uint) -> Vec<f32> {
        let offset = i * self.columns.len();
        std::vec::raw::from_buf(self.data.offset(offset as int) 
                as *const f32, 
            self.columns.len())
    }

    unsafe fn reserve(&mut self, units : uint) {
        if (units * 4 > self.size as uint) {
            let size = self.size * 2;
            libc::ftruncate(self.file, size as i64);
            self.size = size;
            self.data = mmap(self.file, size) as *mut f32;
            self.reserve(units);
        } 
    }

    fn nr(&self) -> uint { self.rows.len() }
    fn nc(&self) -> uint { self.columns.len() }
}

impl Drop for Matrix {
    fn drop(&mut self) {
        unsafe {
            posix::munmap(self.data as *mut u8, self.size);
            libc::close(self.file);
        }
    }
}

impl Collection for Matrix {
    fn len(&self) -> uint {
        self.rows.len() * self.columns.len()
    }

    fn is_empty(&self) -> bool {
        self.len() == 0
    }
}

fn select() {
    let opts = [
        reqopt("m", "matrix", "Matrix directory", "<dir>"),
        optopt("r", "rows", "File containing list of row names", 
            "<file>"),
        optopt("c", "columns", "File containing list of column names",
            "<file>")
    ];
    let matches = match getopts(args().tail(), opts) {
        Ok(m) => {m},
        Err(f) => { fail!(f.to_string()); }
    };
    let path = Path::new(matches.opt_str("m").unwrap());

   
    unsafe {
        let m = Matrix::open(path).unwrap();

        let rows : Vec<uint> = match matches.opt_present("r") {
            true => {
                let path = Path::new(matches.opt_str("r").unwrap());
                positions_from_file(path, m.rows.clone())
            },
            false => range(0, m.rows.len()).collect()
        };

        let columns : Vec<uint> = match matches.opt_present("c") {
            true => {
                let path = Path::new(matches.opt_str("c").unwrap());
                positions_from_file(path, m.columns.clone())
            },
            false => range(0, m.columns.len()).collect()
        };
     
        for &j in columns.iter() {
            print!("\t{}", m.columns.get(j));
        }
        print!("\n");

        for &i in rows.iter() {
            print!("{}", m.rows.get(i));
            let r = m.irow(i);
            for &j in columns.iter() {
                print!("\t{}", r.get(j));
            }
            print!("\n");
        }
    }
}

fn load(path : Path) {
    unsafe {
        let mut m = Matrix::open(path).unwrap();
        let mut rdr = btk::SeriesReader::new(stdin());
        m.set_columns(rdr.index.names.clone());
        let mut n : uint = 0;
        for series in rdr {
            m.append(series);
            n += 1;
            if n % 100 == 0 {
                //println!("* {} rows loaded", n);
                m.write_indices();
            }
        }
        m.write_indices();
    }
}

fn main() {
    let method = args()[1].clone();
    if method == "load".to_string() {
        let path = Path::new(args()[2].clone());
        load(path)
    } else if method == "select".to_string() {
        select()
    }
}
