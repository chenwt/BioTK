#include <iostream>
#include <vector>
#include <set>
#include <fstream>
#include <sstream>
#include <memory>
#include <algorithm>

#include <BioTK/text/AhoCorasick.hpp>

namespace BioTK {
    namespace text {
        namespace AhoCorasick {

using namespace std;

int Node::depth() {
	if (parent == NULL)
		return 0;
	return parent->depth() + 1;
}

shared_ptr<Node>
Node::find(char c) {
	for (int i=0; i<children.size(); i++) {
		if (children[i]->content == c)
			return children[i];
	}
	return NULL;
};

shared_ptr<Node>
Node::find_or_fail(char c) {
	shared_ptr<Node> result = find(c);
	if (result == NULL) {
		return fail;
	} else {
		return result;
	}
}

void Trie::add(string id, string s) {
	shared_ptr<Node> current = root;
	if (!case_sensitive)
		transform(s.begin(), s.end(), s.begin(), ::tolower);
	for (int i=0; i<s.length(); i++) {
		shared_ptr<Node> child = current->find(s[i]);
		if (child == NULL) {
			shared_ptr<Node> c(new Node(s[i]));
			child = c;
			current->children.push_back(child);
			child->parent = current;
		}
		current = child;
	}
	current->terminal = true;
	current->id = id;
}

void Trie::add_fail_transitions(shared_ptr<Node> node) {
	vector<shared_ptr<Node> > children = node->children;
	shared_ptr<Node> child;
	shared_ptr<Node> parent_tsn;
	for (int i=0; i<children.size(); i++) {
		child = children[i];
		if (node == root) {
			child->fail = root;
		} else {
			parent_tsn = node->fail->find(child->content);
			if (parent_tsn == NULL)
				child->fail = root;
			else
				child->fail = parent_tsn;
		}
		add_fail_transitions(child);
	}
}

void Trie::build() {
	add_fail_transitions(root);
	root->fail = root;
}

set<int> word_boundaries(const string& s) {
	set<int> b;
	for (int i=0; i<s.size()-1; i++)
		if (s[i]==' ' && s[i+1]!=' ')
			b.insert(i);	
	return b;
}

vector<Match>
Trie::search(string s) {
	vector<Match> matches;
	if (s.size() == 0)
		return matches;

	set<int> boundaries;
	if (break_on_word_boundaries)
		boundaries = word_boundaries(s);

	if (!case_sensitive)
		transform(s.begin(), s.end(), s.begin(), ::tolower);

	shared_ptr<Node> current = root;	
	for (int i=0; i<s.length(); i++) {
		current = current->find_or_fail(s[i]);
		if (current->terminal) {
			Match match;
			match.id = current->id;
			match.start = i + 1 - current->depth();
			match.end = i;
			if (break_on_word_boundaries) {
				if  (match.start != 0 &&
                        (boundaries.find(match.start-1) 
                            == boundaries.end()))
                    continue;
                if (match.end != s.size()-1 &&
                        boundaries.find(match.end+1) 
                            == boundaries.end())
					continue;
			}
			matches.push_back(match);
		} else if (s[i] == ' ') {
            current = root;
        }
	}
	return matches;
}

struct match_length_key {
	inline bool operator() (const Match& m1, const Match& m2) {
		return m1.length() > m2.length();
	}
};

vector<Match>
remove_overlaps(vector<Match>& v) {
	sort(v.begin(), v.end(), match_length_key());
	vector<Match> out;
	for (Match m1 : v) {
		bool add = true;
		for (Match m2 : out)
			if (!m1.overlaps(m2))
				add = false;
		if (add)
			out.push_back(m1);
	}
	return out;
}

}
}
}
