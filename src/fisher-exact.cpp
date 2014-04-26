#include <apop.h>

#include <cmath>
#include <iostream>

using namespace std;

/* 
 * TODO:
 * - skip odds ratio if ctable isn't 2x2
 * - add a --hybrid flag to fall back to chi-square for large ctables
 */

int main() {
    apop_data* ct = apop_text_to_data("/dev/stdin", 
            .has_row_names='n', 
            .has_col_names='n', 
            .field_ends=NULL, 
            .delimiters="\t");
    apop_data * rs = apop_test_fisher_exact(ct);
    double p = apop_data_get(rs, 0);
    // OR = (a * d) / (b * c)
    // Only used in 2x2 tables
    double odds_ratio = 
        (apop_data_get(ct, 0, 0) * apop_data_get(ct, 1, 1)) / 
        (apop_data_get(ct, 0, 1) * apop_data_get(ct, 1, 0));

    cout << "P-Value\t" << log10(p) << endl;
    cout << "Odds Ratio\t" << log10(odds_ratio) << endl;

    apop_data_free(ct);
    apop_data_free(rs);
}
