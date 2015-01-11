#include <fstream>
#include <iostream>
#include <sstream>
#include <vector>
#include <cassert>
#include <stdio.h>

#include <BioTK.hpp>

using namespace std;
using namespace BioTK::text::AhoCorasick;

/*
void test() {
	string s = "he likes his caffeine she hers";
	vector<Match> result = t.search(s);
	for (int i=0; i<result.size(); i++) {
		cout << result[i].id << "\t" << result[i].start 
            << "\t" << result[i].end << endl;
	}
	return 0;
}
*/

set<string> get_stopwords() {
    FILE* h = popen("aspell -d en_US.multi dump master | aspell -l en -d en_US.multi expand", "r");
    assert(h != NULL);
    set<string> words;
    size_t n = 0;
    char* line = NULL;
    while ((getline(&line, &n, h)) != -1) {
        string s(line, n);
        s.erase(s.find_last_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-'")+1);
        if (!s.empty())
            words.insert(s);
        free(line);
        line = NULL;
    }
    int rc = pclose(h);
    return words;
}

void usage() {
    cerr << 
        "USAGE: tmatch [-i path] [-s path] < input\n"
        "Find multiple terms in input text.\n\n"
        "Arguments:\n"
        "   -i <path> : Path to file containing terms to be searched case insensitively\n"
        "   -s <path> : Path to file containing terms to be searched case sensitively\n"
        "   -h : Show this help\n\n"
        "Input formats:\n"
        "   stdin : The text to be searched. Must have at least two columns, tab delimited.\n"
        "           The first is the record key, and the remaining columns contain text.\n"
        "   term files : Two columns, tab delimited.\n"
        "                Column 1: integer term ID\n"
        "                Column 2: text of the term\n";
    exit(1);
}

const int MIN_SYNONYM_LENGTH = 5;

void populate_trie(Trie& t, const string path, const set<string>& stopwords) {
	ifstream file(path);
	string line;
	while (getline(file, line)) {
        vector<string> fields = BioTK::split(line);
        int id = atoi(fields[0].c_str());
        if (fields[1].size() < MIN_SYNONYM_LENGTH) {
            continue;
        }
        if (stopwords.find(fields[1]) != stopwords.end()) {
            continue;
        }
        if (stopwords.find(BioTK::lowercase(fields[1])) != stopwords.end()) {
            continue;
        }
        t.add(id, fields[1]);
	}
	t.build();
}

int main(int argc, char* argv[]) {
    string cs_path = "", ci_path = "";
    int c;
    while ((c = getopt(argc, argv, "i:s:")) != -1) {
        switch (c) {
            case 'i':
                ci_path = string(optarg);
                break;
            case 's':
                cs_path = string(optarg);
                break;
            case 'h':
                usage();
                break;
        }
    }

    if (cs_path.empty() && ci_path.empty())
        usage();

    set<string> stopwords = get_stopwords();

    string line;
	Trie ci(false, false, true);
    Trie cs(true, false, true);
    if (!cs_path.empty())
        populate_trie(cs, cs_path, stopwords);
    if (!ci_path.empty())
        populate_trie(ci, ci_path, stopwords);

    while (getline(cin, line)) {
        vector<string> fields = BioTK::split(line);
        string key = fields[0];
        string text = "";
        for (int i=1; i<fields.size(); i++) {
            if (i > 1)
                text.append(" ");
            text.append(fields[i]);
        }
        vector<Match> raw_matches = cs.search(text);
        for (Match m : ci.search(text)) {
            raw_matches.push_back(m);
        }
        vector<Match> matches = remove_overlaps(raw_matches);

        set<int> hits;
        for (Match m : matches) {
            hits.insert(m.id);
        }
        for (int hit : hits) {
            cout << key << "\t" << hit << endl;
        }
    }
}
