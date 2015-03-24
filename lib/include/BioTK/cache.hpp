#pragma once

#include <leveldb/db.h>

#include "BioTK/common.hpp"
#include "BioTK/util.hpp"

namespace BioTK {
namespace cache {

const path_t DEFAULT_DIR = 
    "~/.cache/BioTK/";
};

class DownloadCache {
    path_t dir;

public:
    DownloadCache(path_t dir=BioTK::cache::DEFAULT_DIR+"download/") 
            : dir(expanduser(dir)) {
        mkdir_p(expanduser(dir));
    };

    void fetch(std::ifstream&, url_t);
    std::string fetch_path(url_t);
};

template <typename KeyT, typename ValueT>
class KVStore {
    leveldb::DB* db;
    leveldb::Options opt;
    leveldb::WriteOptions wopt;
    leveldb::ReadOptions ropt;
    leveldb::Status status;

public:
    KVStore(path_t _path) {
        opt.create_if_missing = true;
        std::string path = expanduser(_path);
        leveldb::DB::Open(opt, path, &db);
    }

    ~KVStore() {
        delete db;
    }

    bool empty() {
        leveldb::Iterator* it = db->NewIterator(ropt);
        bool is_empty = true;
        for (it->SeekToFirst(); it->Valid(); it->Next()) {
            is_empty = false;
            break;
        }
        delete it;
        return is_empty;
    }

    void 
    put(KeyT& k, ValueT& v) {
        leveldb::Slice s_k((char*) &k, sizeof(KeyT));
        std::string v_ser = serialize(v);
        leveldb::Slice s_v((char*) &v_ser, v_ser.size());
        status = db->Put(wopt, s_k, s_v);
    }

    std::shared_ptr<ValueT>
    get(KeyT& k) {
        leveldb::Slice s_k((char*) &k, sizeof(KeyT));
        std::string v;
        status = db->Get(ropt, s_k, &v);
        std::shared_ptr<ValueT> o;
        if (status.ok()) {
            ValueT* p = new ValueT;
            deserialize(v, *p);
            o = std::shared_ptr<ValueT>(p);
        }
        return o;
    }
};

};
