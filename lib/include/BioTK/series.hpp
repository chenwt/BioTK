#pragma once

#include <string>
#include <map>
#include <set>
#include <vector>
#include <cassert>
#include <memory>

#include <armadillo>

namespace BioTK {

class Index {
public:
    std::map<std::string, size_t> map;
    std::vector<std::string> labels;

    void initialize(std::vector<std::string> labels_) {
        assert(labels.empty());
        labels = labels_;
        for (size_t i=0; i<labels.size(); i++) {
            map[labels[i]] = i;
        }
    }
};

class Series {
private:
    std::shared_ptr<const Index> p_ix;
    const arma::vec* _vdata = NULL;

public:
    std::string key;
    // data is all data (same N as columns), vdata_ is NaNs-removed
    const arma::vec data;

    Series(std::string key, std::shared_ptr<const Index> p_ix, arma::vec data) : 
        key(key), p_ix(p_ix), data(data)
    {
        assert(data.size() == p_ix->labels.size());
    }

    ~Series() {
        if (_vdata != NULL) {
            delete _vdata;
        }
    }

    const Index& index() {
        return *p_ix;
    }

    const arma::vec& vdata() {
        if (_vdata == NULL) {
            _vdata = new arma::vec(data.elem(arma::find_finite(data)));
        }
        return *_vdata;
    }

    double operator[](size_t i) {
        return data[i];
    }

    double operator[](std::string& q) {
        if (p_ix->map.find(q) != p_ix->map.end()) {
            size_t ix = p_ix->map.at(q);
            return data[ix];
        }
        return nan("");
    }

    size_t size() {
        return data.size();
    }

    size_t valid() {
        return vdata().size();
    }

    double sum() { 
        return valid() > 0 ? arma::sum(vdata()) : nan("");
    }

    double mean() { 
        return valid() > 0 ? arma::mean(vdata()) : nan("");
    }

    double std() { 
        return valid() > 2 ? arma::stddev(vdata()) : nan("");
    }

    double median() { 
        return valid() > 0 ? arma::median(vdata()) : nan("");
    }

    Series standardize() {
        return Series(key, p_ix, (arma::vec) (data - mean()) / std());
    }

    double gini() {
        arma::vec v = arma::sort(vdata());
        int n = v.size();
        if (n <= 1) {
            return nan("");
        }
        v += (1 - arma::min(v));
        double g = 2 * arma::dot(arma::linspace(1, n+1, n), v);
        g /= (n * arma::sum(v));
        g -= ((n + 1) / n);
        assert (g >= 0 && g <= 1);
        return g;
    }

    double cor(Series& o) {
        std::set<std::string> ks1 = std::set<std::string>(p_ix->labels.begin(), 
                p_ix->labels.end());
        std::set<std::string> ks2 = std::set<std::string>(o.p_ix->labels.begin(), 
                o.p_ix->labels.end());
        std::vector<double> v1, v2;
        for (std::string k : ks1) {
            if (ks2.find(k) != ks2.end()) {
                if (!isnan(operator[](k)) && !isnan(o[k])) {
                    v1.push_back(operator[](k));
                    v2.push_back(o[k]);
                }
            }
        }
        if (v1.size() < 3)
            return nan("");
        arma::vec rs = arma::cor(arma::vec(v1), arma::vec(v2));
        return rs[0];
    }
};

}
