#pragma once

#include <string>
#include <set>
#include <map>

namespace BioTK {
namespace iridescent {

#include "BioTK/iridescent/article.hpp"
#include "BioTK/iridescent/document_iterator.hpp"

typedef std::string DocumentID;
typedef std::string TermID;
typedef std::map<TermID, std::set<std::string> > lexicon_t;
typedef std::map<TermID, std::set<std::string> > synonym_map_t;
typedef std::map<TermID, std::set<DocumentID> > postings_t;

class TermLexicon {
private:
    postings_t read_postings();

public:
    const std::string root, key;

    TermLexicon(std::string root, std::string key) : root(root), key(key) {};

    bool exists();
    void index_postings(DocumentIterator& iter);
    void initialize(std::string input_path, DocumentIterator& iter);
    synonym_map_t synonym_map();
    postings_t postings();
};

int main(int argc, char* argv[]);

}; // ns iridescent
}; // ns BioTK
