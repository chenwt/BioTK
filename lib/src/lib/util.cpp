#include <wordexp.h>
#include <fstream>
#include <dirent.h>

#include <BioTK/util.hpp>

namespace BioTK {

std::vector<std::string> 
split(const std::string &text, char sep) {
    std::vector<std::string> tokens;
    int start = 0, end = 0;
    while ((end = text.find(sep, start)) != std::string::npos) {
        tokens.push_back(text.substr(start, end - start));
        start = end + 1;
    }
    tokens.push_back(text.substr(start));
    return tokens;
}

std::string lowercase(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), ::tolower);
    return s;
}

std::string uppercase(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), ::toupper);
    return s;
}

/* Filesystem */

int mkdir_p(std::string path) {
    char cmd[1000];
    sprintf(cmd, "/usr/bin/mkdir -p %s", path.c_str());
    return system(cmd);
}

std::string expanduser(std::string path) {
    wordexp_t exp_result;
    wordexp(path.c_str(), &exp_result, 0);
    std::string rs = std::string(exp_result.we_wordv[0]);
    wordfree(&exp_result);
    return rs;
}

bool path_exists(std::string path) {
    std::ifstream f(path.c_str());  
    return f.is_open();
}

// FIXME: handle binary files
void copy_file(path_t src, path_t dest) {
    std::string line;
    std::ifstream in(expanduser(src));
    std::ofstream out(expanduser(dest));
    while (getline(in, line)) {
        out << line << std::endl;
    }
}

std::vector<path_t> 
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

}
