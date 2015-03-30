#include <BioTK.hpp>

using namespace std;

void pivot_matrix(string fill_value="") {
    map<string, map<string, string> > data;

    string line;
    size_t nc = 0;

    while (getline(cin, line)) {
        vector<string> fields = BioTK::split(line);
        if (nc == 0) {
            nc = fields.size();
            if (nc == 2 && fill_value.empty())
                fill_value = "0";
        } else {
            assert(fields.size() == nc);
        }

        if (nc > 2) {
            data[fields[0]][fields[1]] = fields[2];
        } else {
            data[fields[0]][fields[1]] = "1";
        }
    }

    set<string> columns;
    for (auto& p1 : data) {
        for (auto& p2 : p1.second) {
            columns.insert(p2.first);
        }
    }
    for (auto& c : columns)
        cout << "\t" << c;
    cout << endl;

    for (auto& p : data) {
        cout << p.first;
        for (auto& c : columns) {
            cout << "\t";
            auto it = p.second.find(c);
            if (it == p.second.end())
                cout << fill_value;
            else
                cout << it->second;
        }
        cout << endl;
    }
}

void pivot_list(bool deduplicate) {
    map<string, vector<string> > map;

    string line;
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

int main(int argc, char* argv[]) {
    int c;
    bool deduplicate = false;
    bool output_matrix = false;
    string fill_value = "";

    while ((c = getopt(argc, argv, "umv:")) != -1) {
        switch (c) {
            case 'u':
                deduplicate = true;
                break;
            case 'm':
                output_matrix = true;
                break;
            case 'v':
                fill_value = string(optarg);
                break;
        }
    }

    if (output_matrix) {
        pivot_matrix(fill_value);
    } else {
        pivot_list(deduplicate);
    }
}
