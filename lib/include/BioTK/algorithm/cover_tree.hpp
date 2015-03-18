#pragma once

#include <vector>
#include <cmath>
#include <utility>
#include <set>
#include <cfloat>
#include <algorithm>

#include <armadillo>

namespace BioTK {
namespace cover_tree {

typedef double (*distance_metric_t)(const arma::vec&, const arma::vec&);

size_t vector_hash(const arma::vec& v);

class Point {
public:
    size_t id;
    arma::vec data;
    Point(size_t id, const arma::vec& data) : 
        id(id), data(data) {};
};

class Node {
    friend class Point;

public:
    size_t hash;
    std::vector<Point> points;
    std::map<size_t, std::vector<Node*> > children;

    Node(const Point& point) {
        points.push_back(point);
        hash = vector_hash(point.data);
    };

    std::vector<Node*> get_children(size_t level) {
        if (children.find(level) == children.end())
            return std::vector<Node*>();
        return children[level];
    }

    void add_point(const Point& point) {
        for (Point& p : points)
            if (p.id == point.id)
                return;
        points.push_back(point);
    } 

    std::vector<Node*> descendants() {
        std::vector<Node*> o;
        for (auto pair : children) {
            o.insert(o.end(), 
                    pair.second.begin(), pair.second.end());
        }
        return o;
    }
};

typedef std::pair<double, Node*> distance_t;

class Tree {
    friend class Point;
    friend class Node;

    double max_distance;
    distance_metric_t metric_fn;
    static const double base = 2.0;
    size_t min_level, max_level;
    size_t node_count = 0;
    Node* root = NULL;


    bool insert(const Point& point);
    bool insert(const Point&, std::vector<distance_t>&, size_t);
    std::vector<Node*> k_nearest_nodes(const arma::vec&, size_t);

public:
    Tree(distance_metric_t metric, double max_distance) : 
            metric_fn(metric), max_distance(max_distance) {
        max_level = ceilf(log(max_distance) / log(base));
        min_level = max_level - 1;
    };

    ~Tree();

    void insert(size_t id, const arma::vec& data);

    std::vector<size_t> k_nearest(const arma::vec&, size_t k);
};

};

typedef BioTK::cover_tree::Tree CoverTree;

};
