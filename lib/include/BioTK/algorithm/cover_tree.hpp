#pragma once

#include <vector>
#include <cmath>
#include <utility>
#include <set>
#include <cfloat>
#include <algorithm>
#include <unordered_map>

#include <armadillo>

namespace BioTK {
namespace cover_tree {

typedef double (*distance_metric_t)(const arma::vec&, const arma::vec&);
typedef int64_t level_t;
typedef size_t id_t;

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
    std::unordered_map<level_t, std::vector<Node*> > children;
    Node* parent = NULL;
    level_t level;

    Node(const Point& point, level_t level) : level(level) {
        points.push_back(point);
        hash = vector_hash(point.data);
    };

    std::vector<Node*> get_children(level_t level) {
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
    const double base;
    level_t min_level, max_level;
    Node* root = NULL;
    std::map<id_t, Node*> id_index;

    bool insert(const Point& point);
    bool insert(const Point&, std::vector<distance_t>&, level_t);
    std::vector<Node*> k_nearest_nodes(const arma::vec&, size_t);

public:
    Tree(distance_metric_t metric, double max_distance, double base=2.0) : 
            metric_fn(metric), max_distance(max_distance), base(base) {
        max_level = ceil(log(max_distance) / log(base));
        min_level = max_level - 1;
    };

    ~Tree();

    size_t size();
    void add(size_t id, const arma::vec& data);

    std::vector<id_t> k_nearest(const arma::vec&, size_t);
    std::vector<id_t> k_nearest(id_t, size_t);
};

};

typedef BioTK::cover_tree::Tree CoverTree;

};
