function render(makeChart, anchor, data, params) {
    nv.addGraph(function() {
        var chart = makeChart();

        chart.xAxis.axisLabel(params.xlabel);

        chart.yAxis.axisLabel(params.ylabel);

        d3.select(anchor + " svg")
              .datum(data)
              .call(chart);

        nv.utils.windowResize(chart.update);
        return chart;
    });
}

function scatter(anchor, data, params) {
    return render(function() {
        var chart = nv.models.scatterChart()
            .color(d3.scale.category10().range());

        chart.tooltipContent(function(key, x, y, e, graph) {
            return '<h3>GSM' + e.point.id + '</h3>';
        });

        if ("onClick" in params) {
            chart.scatter.dispatch.on("elementClick", params.onClick);
        }

        chart.xAxis
            .tickFormat(d3.format('.02f'));
        chart.yAxis
            .tickFormat(d3.format('.02f'))
            .axisLabelDistance(20);

        //We want to show shapes other than circles.
        //chart.scatter.onlyCircles(false);

        return chart;
    }, anchor, data, params);
}

function bar(anchor, data, x, y, params) {
    return render(function() {
        var chart = nv.models.discreteBarChart()
            .x(function(d) { return d[x]; })
            .y(function(d) { return d[y]; })
            .staggerLabels(true)    
            .showValues(true)       
            .transitionDuration(350)
            ;

        chart.tooltipContent(function(key, x, y, e, graph) {
            return '<h3> n = ' + e.point.Count + '</h3>';
        });

        chart.yAxis.axisLabelDistance(30);

        return chart;
    }, anchor, data, params);
}

function renderPlots() {
    $("div.plot", "div.scatter").each(function() {
        var e = $(this);
        var data = $.parseJSON(e.attr("data"));
        scatter("#chart", data, 
            { xlabel: e.attr("x-label"),
              ylabel: e.attr("y-label"),
              onClick: function(e) { 
                  window.open("/sample/" + e.point.id); 
              } 
            }
        );
    });

    /*
    bar("#tissue-age-expression-correlation", tissueData,
        "Tissue", "Age Correlation",
        {
            ylabel: "Correlation (Pearson R)"
        });

    bar("#tissue-mean-expression", tissueData,
        "Tissue", "Mean Expression",
        {
            ylabel: "Mean Expression (Z-Score)"
        });
    */
}
