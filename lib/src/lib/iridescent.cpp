#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define CFISH_USE_SHORT_NAMES
#define LUCY_USE_SHORT_NAMES

#include "Clownfish/String.h"
#include "Clownfish/VArray.h"
#include "Clownfish/Hash.h"

#include "Lucy/Analysis/EasyAnalyzer.h"
#include "Lucy/Index/Lexicon.h"
#include "Lucy/Document/Doc.h"
#include "Lucy/Index/Indexer.h"
#include "Lucy/Index/IndexReader.h"
#include "Lucy/Index/SegReader.h"
#include "Lucy/Index/DocReader.h"
#include "Lucy/Index/LexiconReader.h"
#include "Lucy/Plan/FullTextType.h"
#include "Lucy/Plan/StringType.h"
#include "Lucy/Plan/Schema.h"
#include "Lucy/Search/Hits.h"
#include "Lucy/Search/IndexSearcher.h"
#include "Lucy/Store/Folder.h"

#include <iostream>
#include <vector>
#include <limits>
#include <set>
#include <map>
#include <cassert>
#include <fstream>

#include <BioTK.hpp>

using namespace std;

namespace BioTK {
namespace iridescent {

/* Globals */

bool LUCY_INITIALIZED = false;

const char* DEFAULT_PATH = 
    "~/.local/share/iridescent";

/* Lucy helpers */

String* lstr(string s) {
    return Str_new_from_utf8(s.c_str(), strlen(s.c_str()));
}

String* lstr(char* s) {
    return lstr(string(s));
}

string extract_field(HitDoc* hit, char* field) {
    String* field_str = lstr(field);
    String* value_str = (String*) HitDoc_Extract(hit, field_str);
    char* value = Str_To_Utf8(value_str);
    string rs(value);
    DECREF(field_str);
    DECREF(value_str);
    return rs;
}

/* Helpers */

synonym_map_t read_synonym_map(string path) {
    lexicon_t lex;
    ifstream in(path.c_str());
    string line;
    while (getline(in, line)) {
        vector<string> fields = BioTK::split(line);
        assert(fields.size() == 2);
        lex[fields[0]].insert(fields[1]);
    }
    return lex;
}

Schema* article_schema() {
    string ft_fields[] = {"title", "abstract"};

    Schema* schema = Schema_new();
    String       *language = Str_newf("en");
    EasyAnalyzer *analyzer = EasyAnalyzer_new(language);

    // ID field
    StringType* str_type = StringType_new();
    String* field_str = lstr("id");
    Schema_Spec_Field(schema, field_str, (FieldType*) str_type);
    DECREF(field_str);

    // Full-text fields
    FullTextType *ft_type = FullTextType_new((Analyzer*)analyzer);
    for (int i=0; i<2; i++) {
        {
            String *field_str = lstr(ft_fields[i]);
            Schema_Spec_Field(schema, field_str, 
                    (FieldType*)ft_type);
            DECREF(field_str);
        }
    }

    DECREF(language);
    DECREF(analyzer);
    DECREF(ft_type);
    DECREF(str_type);
    return schema;
}

/* API */

Article::Article(HitDoc* doc)
{
    id = extract_field(doc, "id");
    title = extract_field(doc, "title");
    abstract = extract_field(doc, "abstract");
}

class DocumentIterator {
    String* ix_path;
    IndexReader* ix_reader;
    VArray* seg_readers;
    String* cls = Str_newf("Lucy::Index::DocReader");
    SegReader* seg_reader;
    DocReader* doc_reader;
    int nseg, ndoc, segi, doci;
    Article* current = NULL;

    void load_segment(int seg_num) {
        seg_reader = (SegReader*) VA_Fetch(seg_readers, seg_num);
        ndoc = SegReader_Doc_Count(seg_reader);
        doc_reader = (DocReader*) SegReader_Obtain(seg_reader,
                cls);
        doci = 0;
        segi = seg_num;
    }

public:
    DocumentIterator(string index_path) {
        ix_path = lstr(index_path.c_str());
        ix_reader = IxReader_open((Obj*) ix_path, NULL, NULL);
        seg_readers = IxReader_Seg_Readers(ix_reader);
        nseg = VA_Get_Size(seg_readers);
        assert(nseg > 0);
        load_segment(0);
    }

    ~DocumentIterator() {
        // TODO: what to decref?
        DECREF(cls);
        DECREF(ix_reader);
    }

    Article* next() {
        if (doci < ndoc) {
            if (current != NULL) {
                delete current;
            }
            HitDoc* doc = DocReader_Fetch_Doc(doc_reader, doci);
            current = new Article(doc);
            doci++;
            DECREF(doc);
            return current;
        } else if (segi < (nseg - 1)) {
            load_segment(segi+1);
            return next();
        } else {
            return NULL;
        }
    }
};

postings_t
TermLexicon::read_postings() {
    postings_t postings;
    string line;
    string postings_path = root + "/postings/" + key;
    assert(BioTK::path_exists(postings_path));
    ifstream in(postings_path);

    while (getline(in, line)) {
        vector<string> fields = BioTK::split(line);
        string key = fields[0];
        for (int i=1; i<fields.size(); i++)
            postings[key].insert(fields[i]);
    }
    return postings;
}

void 
TermLexicon::index_postings(DocumentIterator& iter) {
    string postings_path = root + "/postings/" + key;
    postings_t postings;
    synonym_map_t lexicon = synonym_map();
    BioTK::text::AhoCorasick::Trie trie(false, false, true);
    for (auto pair : lexicon) {
        string key = pair.first;
        for (string synonym : pair.second) {
            trie.add(key, synonym);
        }
    }
    trie.build();
    cerr << "* trie built" << endl;

    Article* article;
    while ((article = iter.next()) != NULL) {
        string document_id = article->id;
        string text = article->text();
        auto matches = trie.search(text);
        for (auto& match : matches) {
            postings[match.id].insert(document_id);
        }
    }
    cerr << "* postings accumulated" << endl;
    cerr << "* saving postings" << endl;

    ofstream out(postings_path);
    for (auto& pair : postings) {
        out << pair.first;
        for (auto& document_id : pair.second) {
            out << "\t" << document_id;
        }
        out << endl;
    }
    cerr << "* matches found for " 
        << postings.size() << " terms." << endl;
}

bool
TermLexicon::exists() {
    return BioTK::path_exists(root + "/lexicon/" + key);
}
    
void 
TermLexicon::initialize(string input_path, DocumentIterator& iter) {
    string path = root + "/lexicon/" + key;
    BioTK::copy_file(input_path, path);
    cerr << "* synonym map copied" << endl;
    index_postings(iter);
}

synonym_map_t 
TermLexicon::synonym_map() {
    return read_synonym_map(root + "/lexicon/" + key);
}

postings_t 
TermLexicon::postings() {
    // FIXME: memoize
    string postings_path = root + "/postings/" + key;
    assert(BioTK::path_exists(postings_path));
    return read_postings();
}

class IRIDESCENT {
private:
    string path;
    String* folder = NULL;
    Indexer *indexer = NULL;
    Schema* schema = NULL;
    IndexSearcher* searcher = NULL;
    vector<TermLexicon> _lexicons;

    void add_element(Doc* doc, string field, string data) {
        String* field_str = lstr(field);
        String* data_str = lstr(data);
        Doc_Store(doc, field_str, (Obj*) data_str);
        DECREF(field_str);
        DECREF(data_str);
    }

    void load_lexicons() {
        _lexicons.clear();
        for (BioTK::path_t p : 
                BioTK::listdir(path + "/lexicon/")) {
            string key = string(basename(p.c_str()));
            _lexicons.push_back(TermLexicon(path, key));
        }
    }

public:
    IRIDESCENT(const char* raw_path=DEFAULT_PATH) {
        if (!LUCY_INITIALIZED) {
            lucy_bootstrap_parcel();
            LUCY_INITIALIZED = true;
        }

        path = BioTK::expanduser(raw_path);
        BioTK::mkdir_p(path);
        BioTK::mkdir_p(path + "/lexicon");
        BioTK::mkdir_p(path + "/postings");
        load_lexicons();

        schema = article_schema();

        string index_path = path + "/index";
        folder = Str_newf(index_path.c_str());
    };

    ~IRIDESCENT() {
        if (searcher != NULL)
            DECREF(searcher);
        if (indexer != NULL)
            DECREF(indexer);
        DECREF(schema);
        DECREF(folder);
    }

    void add(Article& article) {
        if (indexer == NULL) {
            indexer = Indexer_new(schema, (Obj*)folder, NULL,
                    Indexer_CREATE | Indexer_TRUNCATE);
        }
        Doc* doc = Doc_new(NULL, 0);
        add_element(doc, string("id"), article.id);
        add_element(doc, string("title"), article.title);
        add_element(doc, string("abstract"), article.abstract);
        Indexer_Add_Doc(indexer, doc, 1.0);
        DECREF(doc);
        cerr << "+" << article.id << endl;
    }

    TermLexicon& lexicon(string key) {
        for (TermLexicon& lex : _lexicons) {
            if (lex.key == key)
                return lex;
        }
    }

    vector<TermLexicon>& lexicons() {
        return _lexicons;
    }

    void add_lexicon(string key, string input_path) {
        // FIXME: assert lexicon not already extant 
        TermLexicon lexicon(path, key);
        DocumentIterator iter = documents();
        lexicon.initialize(input_path, iter);
        load_lexicons();
    }

    DocumentIterator documents() {
        return DocumentIterator(path + "/index");
    }

    void commit() {
        Indexer_Commit(indexer);
    }

    set<DocumentID> search(string query, bool exact = false) {
        if (exact) {
            char q[1000];
            sprintf(q, "\"%s\"", query.c_str());
            return search(string(q));
        }

        set<DocumentID> rs;

        if (searcher == NULL) {
            searcher = IxSearcher_new((Obj*)folder);
        }

        uint32_t n_wanted = numeric_limits<uint32_t>::max();

        String* q = lstr(query);
        Hits* hits = IxSearcher_Hits(searcher,
                (Obj*) q,
                0, n_wanted, NULL);
        String* field_str = lstr("id");
        HitDoc *hit;

        while ((hit = Hits_Next(hits)) != NULL) {
            String* id = (String*)HitDoc_Extract(hit, field_str);
            char* value = Str_To_Utf8(id);
            rs.insert(string(value));
            free(value);
            DECREF(id);
            DECREF(hit);
        }
        DECREF(field_str);
        DECREF(q);
        DECREF(hits);
        return rs;
    }
};

void index(IRIDESCENT& engine) {
    string line;
    int n = 0;
    while (getline(cin, line)) {
        vector<string> fields = BioTK::split(line);
        Article article(fields[0], fields[1], fields[2]);
        engine.add(article);
        n++;
    }
    engine.commit();
}

void search(IRIDESCENT& engine, char* query) {
    set<DocumentID> hits = engine.search(query);
    for (DocumentID id : hits) {
        cout << id << endl;
    }
}

void similarity(IRIDESCENT& engine, char* query) {
    set<DocumentID> reference = engine.search(query, true);
    vector<TermLexicon>& lexicons = engine.lexicons();
    for (TermLexicon& lexicon : lexicons) {
        postings_t postings = lexicon.postings();

        // FIXME: implement
        double document_count = 4000000;
     
        for (auto pair : postings) {
            const TermID& term_id = pair.first;
            set<DocumentID>& matches = pair.second;
            if (matches.size() < 5)
                continue;

            size_t i = BioTK::intersection_size(reference, matches);
            size_t u = matches.size() + reference.size() - 2 * i;
            double jaccard = 1.0 * i / u;
            double mi = (i * document_count) / 
                (matches.size() * reference.size());
            if (jaccard == 0 || i < 3)
                continue;

            cout << lexicon.key << ":" << term_id 
                << "\t" << i 
                << "\t" << -log10(jaccard)
                << "\t" << log2(mi)
                << endl;
        }
    }
}

void usage(int rc = 0) {
    cerr << "USAGE: iridescent option...\n\n" 
        << "Options:\n"
        << "  -q <query> : query the index for the term\n"
        << "  -s : perform a similarity search for the query\n"
        << "       term specified by the '-q' option\n"
        << "  -l <spec> : load a lexicon into the index,\n"
        << "              where 'spec' = 'key:path'. 'key'\n"
        << "              is a name for the lexicon, and 'path'\n"
        << "              is the path to a tab-delimited file\n"
        << "              containing ID-synonym pairs\n"
        << "  -i : index documents on stdin\n"
        << "  -c : output the documents in the index\n"
        << "  -h : show this help\n"
        ;
    exit(rc);
}

int main(int argc, char* argv[]) {
    char* ix_path = strdup(DEFAULT_PATH);
    char* lexicon_path = NULL;
    char* lexicon_key = NULL;
    vector<string> lexicon_fields;

    bool do_index = false;
    bool cat_documents = false;
    bool show_usage = false;
    bool do_similarity = false;
    char* query = NULL;
    int c;
    while ((c = getopt(argc, argv, "shcl:d:q:i")) != -1) {
        switch (c) {
            case 'c':
                cat_documents = true;
                break;
            case 'i':
                do_index = true;
                break;
            case 'q':
                query = optarg;
                break;
            case 'd':
                ix_path = optarg;
                break;
            case 'l':
                lexicon_fields = BioTK::split(optarg, ':');
                assert(lexicon_fields.size() == 2);
                lexicon_key = strdup(lexicon_fields[0].c_str());
                lexicon_path = strdup(lexicon_fields[1].c_str());
                break;
            case 'h':
                show_usage = true;
                break;
            case 's':
                do_similarity = true;
        }
    }

    IRIDESCENT engine(ix_path);

    if (show_usage) {
        usage(0);
    } else if (do_index) {
        index(engine);
    } else if (query != NULL) {
        if (do_similarity) {
            similarity(engine, query);
        } else {
            search(engine, query);
        }
    } else if ((lexicon_key != NULL) && (lexicon_path != NULL)) {
        engine.add_lexicon(lexicon_key, lexicon_path);
    } else if (cat_documents) {
        DocumentIterator iter = engine.documents();
        Article* article;
        while ((article = iter.next()) != NULL) {
            cout << article->id
                << "\t" << article->title 
                << "\t" << article->abstract
                << endl;
        }
    } else {
        usage(1);
    }
}

};
};
