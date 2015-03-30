#pragma once

#include <leveldb/db.h>

#include "BioTK/common.hpp"
#include "BioTK/util.hpp"
#include "BioTK/config.hpp"

namespace BioTK {

class DownloadCache {
    path_t dir;

public:
    DownloadCache(path_t dir) 
            : dir(expanduser(dir)) {
        mkdir_p(expanduser(dir));
    };

    DownloadCache() {
        std::string CONFIG_ROOT = config("CACHE_ROOT");
        path_t path = CONFIG_ROOT + "/download";
        this->dir = path;
        mkdir_p(dir);
    }


    void fetch(std::ifstream&, url_t);
    std::string fetch_path(url_t);
};

template <typename KeyT, typename ValueT>
class KVStore {
    std::string path;
    leveldb::DB* db;
    leveldb::Options opt;
    leveldb::WriteOptions wopt;
    leveldb::ReadOptions ropt;
    leveldb::Status status;

public:
    class iterator {
        leveldb::Iterator* iter;

    public:
        iterator(leveldb::Iterator* iter) : iter(iter) {
            iter->SeekToFirst();
        };
        ~iterator() { delete iter; }
        
        bool eof() {
            return !iter->Valid();
        }

        void operator++() {
            iter->Next();
        }

        KeyT key() {
            KeyT k;
            deserialize(iter->key().ToString(), k);
            return k;
        }

        ValueT value() {
            ValueT v;
            deserialize(iter->value().ToString(), v);
            return v;
        }
    };

    KVStore(const KVStore& other) : KVStore(other.path) {};

    KVStore(path_t _path) {
        opt.create_if_missing = true;
        path = expanduser(_path);
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

    iterator
    iter() {
        return iterator(db->NewIterator(ropt));
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

template <typename KeyT, typename ValueT>
KVStore<KeyT, ValueT>kvstore(std::string name) {
    std::string CONFIG_ROOT = config("CONFIG_ROOT");
    path_t path = CONFIG_ROOT + "/kv/" + name;
    return KVStore<KeyT,ValueT>(path);
}

};
