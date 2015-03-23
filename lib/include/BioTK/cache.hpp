#pragma once

#include "db_cxx.h"
#include "dbstl_map.h"

#include "BioTK/common.hpp"
#include "BioTK/util.hpp"

namespace BioTK {
namespace cache {

const path_t DEFAULT_DIR = 
    "~/.cache/BioTK/db/";

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

class StoreBase {
protected:
    DbEnv* env = NULL;
    Db* db = NULL;
    bool is_open = false;

    void open(
            const path_t _dir, 
            const std::string name,
            uint32_t db_flags = 0) {
        path_t dir = BioTK::expanduser(_dir);
        mkdir_p(dir);

        uint32_t flags = 
            DB_CREATE | DB_INIT_MPOOL;

        env = new DbEnv(DB_CXX_NO_EXCEPTIONS);
        env->open(dir.c_str(), flags, 0);
        //env->set_error_stream(&cerr);

        uint32_t db_create_flags = 0;
        if (!path_exists(dir + "/" + name))
            db_create_flags |= DB_CREATE;

        db = new Db(env, DB_CXX_NO_EXCEPTIONS);
        if (db_flags)
            db->set_flags(db_flags);
        db->open(NULL, name.c_str(), NULL, 
                DB_BTREE, db_create_flags | db_flags, 0);

        is_open = true;
    }

public:
    virtual ~StoreBase() {
        LOG(INFO) << "closing";
        close();
    }

    void close() {
        if (!is_open)
            return;
        env->close(DB_FORCESYNC);
        is_open = false;
        delete db;
        delete env;
    }

    virtual size_t size() = 0;
};    

template <typename KeyT, typename ValueT>
class KVStore : StoreBase {
    typedef dbstl::db_map<KeyT, ValueT> map_t;
    map_t* map = NULL;

public:
    KVStore(const path_t _dir, const std::string name) {
        open(_dir, name);
        map = new map_t(db, env);
    }

    virtual size_t size() { return map->size(); }

    ValueT get(const KeyT& key) {
        return (*map)[key];
    }

    void put(const KeyT& key, const ValueT& value) {
        (*map)[key] = value;
    }

    ValueT operator[](const KeyT& k) { 
        return get(k); 
    }
};

template <typename KeyT, typename ValueT>
class KVMultiStore : StoreBase {
    typedef dbstl::db_multimap<KeyT, ValueT> map_t;
    typedef typename map_t::iterator iter_t;
    map_t* map = NULL;

public:
    KVMultiStore(const path_t _dir, const std::string name) {
        open(_dir, name, DB_DUP);
        map = new map_t(db, env);
    }

    virtual size_t size() { return map->size(); }

    std::vector<ValueT>
    get(const KeyT& key) {
        std::vector<ValueT> o;
        auto pair = map->equal_range(key);
        for (auto it=pair.first; it != pair.second; it++) {
            o.push_back(it->second);
        }
        return o;
    }

    void 
    add(const KeyT& key, const ValueT& value) {
        map->insert(make_pair(key, value));
    }

    std::vector<ValueT>
    operator[](const KeyT& k) { 
        return get(k); 
    }
};


template<typename KeyT, typename ValueT>
KVStore<KeyT, ValueT>
kvstore(const std::string& name) {
    return KVStore<KeyT,ValueT>(
            BioTK::cache::DEFAULT_DIR, name);
}


};
