from . import *
from .element import *

##############
# Simple views
##############

static_template = lambda tmpl, route: \
        root.route(route)(view(tmpl)(lambda: dict()))

static_template("index", "/")
static_template("tutorial", "/tutorial")

############
# Statistics
############

@view("/statistics", title="Database statistics")
def statistics():
    return view_to_table("channel_data_by_taxon", 
            title="Available Taxa", 
            limit=10,
            link_format="/statistics/{0}")

@view("/statistics/age-distribution/summary",
    title="Age Distribution Summary (Months)")
def age_distribution_summary():
    return sql_to_table("""
            SELECT * FROM age_distribution_summary
            WHERE "N" > 1000;
            """,
            link_format="/statistics/age-distribution/{0}")

@root.get("/statistics/age-distribution/<taxon_id>")
def age_distribution(taxon_id):
    return "baz"

###########
# Changelog
###########

@root.get("/changelog")
@view("changelog", title="Changelog")
def fn():
    return {"commits": itertools.groupby((commit for commit in repo.commits
        if "ui" in commit.tags), lambda c: c.date.date())}

#######
# Plots
#######

@view("/plot")
def fn():
    df = pd.read_csv("bower/components/BioTK/iris.csv")
    s = df.iloc[:5,0]
    s.index = ["a", "b", "c", "d" , "e"]
    df = df.loc[:,["Species","Sepal width", "Petal width"]]
    df.name = "Sepal width vs Petal width"
    return ScatterPlot(df), BarPlot(s)

@view("/plot2")
def fn():
    return Static("plot/scatter")

###############
# Complex views
###############

@view("/search", method="post")
def search():
    q = request.forms["query"]

    if q.isdigit():
        gene_id = int(q)
        redirect("/gene/%s" % gene_id)
    elif q.lower().startswith("go:"):
        # implement for generic terms
        raise Exception("not implemented")
    return fn_to_table("query_gene", q,
            title="Query results - %s" % q,
            link_format="/gene/{0}")

def plot_gene_set(taxon_id, genes):
    pass

@root.get("/gene/<gene_id>")
def gene(gene_id):
    pass

bottle.run(root, host="0.0.0.0", port=8000)
