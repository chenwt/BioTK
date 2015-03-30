#include <cassert>

#include "BioTK/algorithm/cover_tree.hpp"

using namespace std;

namespace BioTK {
namespace cover_tree {

size_t vector_hash(const arma::vec& v) {
    const char* data = (const char*) v.memptr();
    size_t size = v.size() * sizeof(double);
    std::string s(data, size);
    return std::hash<std::string>()(s);
}

Tree::~Tree() {
    if (root == NULL)
        return;
    vector<Node*> nodes;
    nodes.push_back(root);
    while (!nodes.empty()) {
        Node* current = nodes[0];
        nodes.erase(nodes.begin());
        std::vector<Node*> children = current->descendants();
        nodes.insert(nodes.begin(), 
                children.begin(), children.end());
        delete current;
    }
}

size_t 
Tree::size() {
    return id_index.size();
}

void 
Tree::add(id_t id, const arma::vec& data) {
    insert(Point(id, data));
}

bool
Tree::insert(const Point& point, 
        std::vector<distance_t>& Qi, 
        level_t level) {

    std::vector<distance_t> Qj;
    double sep = pow(base, level);
    double min_distance = DBL_MAX;
    distance_t min_qi_distance(DBL_MAX, NULL);

    for (distance_t& qi : Qi) {
        if (qi.first < min_qi_distance.first)
            min_qi_distance = qi;
        min_distance = std::min(qi.first, min_distance);

        if (qi.first <= sep) {
            Qj.push_back(qi);
        } 

        std::vector<Node*> children = 
            qi.second->get_children(level);

        for (Node* child : children) {
            double distance = metric_fn(point.data, 
                child->points[0].data);
            assert(distance > 0);
            min_distance = std::min(distance, min_distance);
            if (distance <= sep)
                Qj.push_back(std::make_pair(distance, child));
        }
    }

    if (min_distance > sep) {
        return false;
    } else {
        bool found = insert(point, Qj, level-1);
        if ((!found) && (min_qi_distance.first <= sep)) {
            min_level = std::min(min_level, level-1);
            Node* new_node = new Node(point, level);
            id_index[point.id] = new_node;
            min_qi_distance.second->
                children[level].push_back(new_node);
            new_node->parent = min_qi_distance.second;
            return true;
        } else {
            return found;
        }
    }
}

bool
Tree::insert(const Point& point) {
    if (root == NULL) {
        root = new Node(point, max_level);
        id_index[point.id] = root;
    } else {
        size_t hash = vector_hash(point.data);
        for (Node* node : root->descendants()) {
            if (node->hash == hash)
                node->points.push_back(point);
        }

        std::vector<distance_t> Qi;
        double distance = 
            metric_fn(point.data, root->points[0].data);
        Qi.push_back(std::make_pair(distance, root));
        insert(point, Qi, max_level);
    }
    return true;
}

std::vector<Node*> 
Tree::k_nearest_nodes(const arma::vec& data, size_t k) {
    if (root == NULL)
        return std::vector<Node*>();
    assert(k <= id_index.size());

    double max_distance = metric_fn(root->points[0].data, 
            data);

    std::set<distance_t> best;
    distance_t root_distance = 
        std::make_pair(max_distance, root);
    best.insert(root_distance);
    std::vector<distance_t> Qj(1, root_distance);

    size_t checked = 0;
    //cerr << endl;

    for (level_t level=max_level; level>=min_level; level--) {
        size_t size = Qj.size();
        for (size_t i=0; i<size; i++) {
            std::vector<Node*> children = 
                Qj[i].second->get_children(level);
            for (Node* child : children) {
                double d = metric_fn(child->points[0].data,
                        data);
                checked++;

                if ((d < max_distance) || (best.size() < k)) {
                    best.insert(std::make_pair(d, child));
                    if (best.size() > k)
                        best.erase(--best.end());
                    max_distance = (--best.end())->first;
                }
                Qj.push_back(std::make_pair(d,child));
            }
        }

        double sep = max_distance + pow(base, level);
        size = Qj.size();
        for (size_t i=0; i<size; i++) {
            if (Qj[i].first > sep) {
                Qj[i] = Qj.back();
                Qj.pop_back();
                size--;
                i--;
            }
        }
        //cerr << "level: " << level << " cs size: " << Qj.size() << " checked: " << checked << endl;
    }

    std::vector<Node*> knn;
    for (auto pair : best) {
        knn.push_back(pair.second);
    }
    return knn;
}

vector<id_t>
Tree::k_nearest(const arma::vec& data, size_t k) {
    vector<Node*> knn = k_nearest_nodes(data, k+1);
    vector<id_t> o;
    for (Node* n : knn) {
        for (Point& p : n->points) {
            o.push_back(p.id);
            if (o.size() == k)
                return o;
        }
    }
    return o;
}

vector<id_t> 
Tree::k_nearest(id_t id, size_t k) {
    Node* node = id_index[id];
    return k_nearest(node->points[0].data, k);
}

/*
vector<id_t>
Tree::k_nearest(id_t id, size_t k) {
    Node* target = id_index[id];
    set<Node*> candidates;
    candidates.insert(target);
    Node* parent = target;

    do {
        for (Node* descendant : parent->descendants()) {
            candidates.insert(descendant);
        }
        parent = parent->parent;
    } while ((candidates.size() < k) && (parent != NULL));

    set<distance_t> distances;
    for (Node* n : candidates) {
        double distance = metric_fn(n->points[0].data, 
                target->points[0].data);
        distances.insert(distance_t(distance, n));
    }

    vector<id_t> o;
    for (auto pair : distances) {
        for (auto point : pair.second->points) {
            o.push_back(point.id);
            if (o.size() == k)
                return o;
        }
    }
    return o;
}
*/

};
};
