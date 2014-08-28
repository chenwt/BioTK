extern crate lcg;

use std::io;

fn main() {
    let mut rows : Vec<Vec<String>> = vec![];
    for wrapper in std::io::stdin().lines() {
        match wrapper {
            Ok(line) => {
                let row : Vec<String> = line.as_slice()
                    .trim_right_chars('\n').split('\t').map(String::from_str)
                    .collect();
                if rows.len() > 0 && row.len() != rows[rows.len()-1].len() {
                    fail!("rows don't have all the same number of fields");
                }
                rows.push(row);
            }
            Err(_) => ()
        }
    }
    let ni = rows.len();
    let nj = rows[0].len();
    for j in range(0, nj) {
        print!("{}", rows[0][j]);
        for i in range(1, ni) {
            print!("\t{}", rows[i][j]);
        }
        print!("\n");
    }
}
