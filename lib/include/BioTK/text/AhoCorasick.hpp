#pragma once

#include <string>
#include <vector>
#include <memory>

namespace BioTK {
    namespace text {
        namespace AhoCorasick {

using namespace std;

class Node {
public:
	Node() {};
	Node(char c) {content = c; terminal = false;}
	int id;
	int depth();
	char content;		
	bool terminal;
	vector<shared_ptr<Node> > children;
	shared_ptr<Node> parent;
	shared_ptr<Node> fail;
	shared_ptr<Node> find(char c);
	shared_ptr<Node> find_or_fail(char c);
};

struct Match {
	int id;
	int start;
	int end;
	int length() const {return end - start;}
	bool overlaps(const Match& o) const {
		return end <= o.start && start < o.end;
	}
};

class Trie {
public:
	Trie(
        bool case_sensitive=false,
        bool remove_overlaps=false,
        bool break_on_word_boundaries=true
    ) : 
        case_sensitive(case_sensitive),
        remove_overlaps(remove_overlaps),
        break_on_word_boundaries(break_on_word_boundaries)
        {
            root = shared_ptr<Node>(new Node());
        };

	vector<Match> search(string s);
	void add(string s);
	void add(int id, string s);
	void build();
private:
    bool case_sensitive,
         remove_overlaps,
         break_on_word_boundaries;
	shared_ptr<Node> root;
	void add_fail_transitions(shared_ptr<Node> n);
};

vector<Match> remove_overlaps(vector<Match>&);

// end namespace
}
}
}
