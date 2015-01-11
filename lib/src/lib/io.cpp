#include <armadillo>

#include <BioTK/io.hpp>
#include <BioTK/util.hpp>

using namespace std;

BioTK::SeriesReader::SeriesReader(std::string path) {
    input.open(path.c_str());
    string header;
    getline(input, header);
    vector<string> labels = BioTK::split(header);
    labels.erase(labels.begin());

    p_index = make_shared<Index>();
    p_index->initialize(labels);
}

BioTK::Series*
BioTK::SeriesReader::next() {
    string line;
    if (getline(input, line) == NULL) {
        return NULL;
    }
    if (current != NULL) {
        delete current;
    }
    std::vector<std::string> fields = BioTK::split(line);

    std::vector<double> elements;
    for (int i=1; i<fields.size(); i++) {
        elements.push_back(atof(fields[i].c_str()));
    }
    current = new BioTK::Series(fields[0], p_index, 
            arma::vec(elements));
    return current;
}

BioTK::SeriesReader::~SeriesReader() {
    if (current != NULL) {
        delete current;
    }
}
