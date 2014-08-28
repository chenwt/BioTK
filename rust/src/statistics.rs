use std::num::{pow};

pub struct Correlation {
    pub r : f32,
    pub p_value : f32,
    pub n : uint
}

pub trait Statistics {
    fn map(&self, f: |&f32|->f32) -> Vec<f32>;

    fn sum(&self) -> f32;
    fn mean(&self) -> f32;
    fn var(&self) -> f32;
    fn std(&self) -> f32;

    fn dropna(&self) -> Vec<f32>;
    fn standardize(&self) -> Vec<f32>;

    fn dot(&self, &Vec<f32>) -> Vec<f32>;
    fn correlate(&self, &Vec<f32>) -> Correlation;
}

/* These functions all assume no NaN */
impl Statistics for Vec<f32> {
    /* Functional */

    fn map(&self, f: |&f32|->f32) -> Vec<f32> {
        self.iter().map(f).collect()
    }

    /* Reductions */

    fn sum(&self) -> f32 {
        self.iter().fold(0.0, |s,&x| s + x)
    }

    fn mean(&self) -> f32 {
        self.sum() / self.len() as f32
    }

    fn var(&self) -> f32 {
        let mu2 = pow(self.mean(), 2);
        self.map(|&x| pow(x, 2) - mu2).sum() / 
            ((self.len() - 1) as f32)
    }

    fn std(&self) -> f32 {
        self.var().sqrt() 
    }

    /* Transformation */

    fn standardize(&self) -> Vec<f32> {
        let clean = self.dropna();
        let mu = clean.mean();
        let stdev = clean.std();
        self.map(|x| (x - mu) / stdev)
    }

    fn dropna(&self) -> Vec<f32> {
        let mut o = self.clone();
        o.retain(|&x| x.is_nan().not());
        o
    }

    /* Pairwise */

    fn dot(&self, y: &Vec<f32>) -> Vec<f32> {
        // FIXME: allocate whole vector
        let mut o = Vec::new();
        for i in range(0, self.len()) {
            o.push(self[i] * y[i]);
        }
        o
    }

    fn correlate(&self, y: &Vec<f32>) -> Correlation {
        let sx = self.standardize();
        let sy = y.standardize();
        let dp : Vec<f32> = sx.dot(&sy).dropna();
        let n = dp.len();
        let r = dp.sum() / ((n - 1) as f32);
        //let t = r / ((1-pow(r,2)).sqrt() / (n - 2));
        Correlation{r:r, p_value:0.5, n:n}
    }
}

/*
pub fn correlate(Vec<f32> x, Vec<f32> y) {
}
*/
