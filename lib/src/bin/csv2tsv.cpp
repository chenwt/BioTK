#include <iostream>

#include <BioTK.hpp>

using namespace std;

int main(){
    // FIXME: doesn't do quoting...
    
    string line;
    while (getline(cin, line)) {
        vector<string> fields = BioTK::split(line, ',');
        cout << fields[0];
        for (int i=1; i<fields.size(); i++) {
            cout << "\t" << fields[i];
        }
        cout << endl;
    }
}
