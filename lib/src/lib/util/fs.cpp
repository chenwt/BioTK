#include <wordexp.h>
#include <dirent.h>
#include <cstdlib>
#include <unistd.h>
#include <linux/limits.h>

#include <fstream>

#include "BioTK/util.hpp"

using namespace std;

namespace BioTK {

bool 
mkdir_p(path_t path) {
    char cmd[1000];
    sprintf(cmd, "/usr/bin/mkdir -p %s", path.c_str());
    bool create = !path_exists(path);
    system(cmd);
    return create;
}

path_t
expanduser(path_t path) {
    wordexp_t exp_result;
    wordexp(path.c_str(), &exp_result, 0);
    std::string rs = std::string(exp_result.we_wordv[0]);
    wordfree(&exp_result);
    return rs;
}

bool 
path_exists(path_t path) {
    std::ifstream f(path.c_str());  
    return f.is_open();
}

void 
copy_file(path_t src, path_t dest) {
    std::string line;
    std::ifstream in(expanduser(src));
    std::ofstream out(expanduser(dest));
    out << in.rdbuf();
}

vector<path_t> 
listdir(path_t dirpath) {
    std::vector<path_t> rs;

    DIR *dir;
    struct dirent *ent;
    if ((dir = opendir (dirpath.c_str())) != NULL) {
          /* print all the files and directories within directory */
          while ((ent = readdir (dir)) != NULL) {
              std::string path(ent->d_name);
              if (path == "." || path == "..")
                  continue;
              rs.push_back(dirpath + "/" + path);
          }
          closedir (dir);
    } else {
        /* could not open directory */
        perror("");
    }
    return rs;
}

path_t 
progname() {
    char *path = (char*) malloc(PATH_MAX);
    if (path != NULL) {
        if (readlink("/proc/self/exe", path, PATH_MAX) == -1) {
            free(path);
            path = NULL;
        }
    }
    return string(basename(path));
}

};
