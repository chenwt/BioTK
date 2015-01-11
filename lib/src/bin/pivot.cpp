#include <BioTK.hpp>

using namespace std;

int main(int argc, char* argv[]) {
    int c;
    map<string, vector<string> > map;
    string line;
    bool deduplicate = false;

    while ((c = getopt(argc, argv, "u")) != -1) {
        switch (c) {
            case 'u':
                deduplicate = true;
                break;
        }
    }

    while (getline(cin, line)) {
        vector<string> fields = BioTK::split(line);
        map[fields[0]].push_back(fields[1]);
    }

    for (auto& pair : map) {
        vector<string>& values = pair.second;
        sort( values.begin(), values.end() );

        if (deduplicate) {
            values.erase(unique(values.begin(), values.end() ), 
                    values.end());
        }

        cout << pair.first;
        for (string& v : values) {
            cout << "\t" << v;
        }
        cout << endl;
    }
}
