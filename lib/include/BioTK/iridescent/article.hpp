#pragma once

#include <string>

#include "Lucy/Document/HitDoc.h"

class Article {
public:
    std::string id, title, abstract;

    Article(std::string id, std::string title, std::string abstract) :
        id(id), title(title), abstract(abstract) {};

    Article(lucy_HitDoc* doc);

    std::string text() {
        return title + " " + abstract;
    }
};


