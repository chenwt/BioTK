#include <BioTK.hpp>

using namespace std;

int main(int argc, char* argv[]) {
    int c;
    string line;
    bool is_matrix = false;

    while ((c = getopt(argc, argv, "m")) != -1) {
        switch (c) {
            case 'm':
                is_matrix = true;
                break;
        }
    }

    if (is_matrix) {
        BioTK::SeriesReader reader("/dev/stdin");
        while (BioTK::Series* s = reader.next()) {
            for (int i=0; i<s->size(); i++) {
                cout << s->key 
                    << "\t" << s->index().labels[i] 
                    << "\t" << s->data[i] << endl;
            }
        }

    } else {
        while (getline(cin, line)) {
            vector<string> fields = BioTK::split(line);
            for (int i=1; i<fields.size(); i++) {
                cout << fields[0] << "\t" << fields[i] << endl;
            }
        }
    }
}
