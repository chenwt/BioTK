#pragma once

#include "db_cxx.h"
#include "dbstl_map.h"

#include "BioTK/common.hpp"
#include "BioTK/util.hpp"

namespace BioTK {
namespace cache {

const path_t DEFAULT_DIR = 
    "~/.local/share/BioTK/cache/";

class DownloadCache {
    path_t dir;

public:
    DownloadCache(path_t dir=DEFAULT_DIR+"download/") 
            : dir(expanduser(dir)) {
        mkdir_p(expanduser(dir));
    };

    void fetch(std::ifstream&, url_t);
    std::string fetch_path(url_t);
};

/*
typedef std::string KeyT;
typedef std::string ValueT;
*/

};

template <typename KeyT, typename ValueT, 
         class MapT = dbstl::db_map<KeyT, ValueT> >
class KVStore {
    DbEnv* env = NULL;
    Db* db = NULL;
    typedef dbstl::db_map<KeyT, ValueT> map_t;
    map_t* map = NULL;
    bool is_open;

public:
    KVStore(const path_t _dir, const std::string name) {
        path_t dir = BioTK::expanduser(_dir);
        mkdir_p(dir);

        uint32_t flags = 
            DB_CREATE | DB_INIT_MPOOL;

        env = new DbEnv(DB_CXX_NO_EXCEPTIONS);
        env->open(dir.c_str(), flags, 0);
        //env->set_error_stream(&cerr);

        uint32_t db_flags = 0;
        if (!path_exists(dir + "/" + name))
            db_flags |= DB_CREATE;

        db = new Db(env, DB_CXX_NO_EXCEPTIONS);
        db->open(NULL, name.c_str(), NULL, 
                DB_BTREE, db_flags, 0);

        map = new map_t(db, env);
        is_open = true;
    }


    ~KVStore() {
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

    ValueT get(const KeyT& key) {
        return (*map)[key];
    }

    void put(const KeyT& key, const ValueT& value) {
        dbstl::begin_txn(0, env);
        (*map)[key] = value;
        dbstl::commit_txn(env);
    }

    size_t size() { return map->size(); }

    ValueT operator[](const KeyT& k) { 
        return get(k); 
    }
};

typedef BioTK::cache::DownloadCache DownloadCache;

template<typename KeyT, typename ValueT>
KVStore<KeyT, ValueT>
kvstore(const std::string& name) {
    return KVStore<KeyT,ValueT>(
            BioTK::cache::DEFAULT_DIR, name);
}


};
