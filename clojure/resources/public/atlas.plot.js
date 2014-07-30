plot = {
    initialize: function(div) {
        var type = div.attr("type");
        var uuid = div.attr("uuid");
        $.post("/ajax/plot", {"uuid": uuid}, function(o) {
            nv.addGraph(function() {
                div.empty();
                div.append("<h4 align='center'></h4><svg></svg>");
                var title = div.children()[0];
                title.innerHTML = o.title;

                var chart = plot[type](o);
                chart.yAxis.axisLabel(o["y-label"]);
                chart.xAxis.axisLabel(o["x-label"]);

                var svg = div.children()[1];
                console.log(o);
                d3.select(svg)
                    .datum(o.data)
                    .call(chart);
                nv.utils.windowResize(chart.update);

                return chart;
            });
        });
    },

    /*
     * Chart types
     */
    
    scatter: function(o) {
        var chart = nv.models.scatterChart()
            .color(d3.scale.category10().range());
        chart.xAxis
            .tickFormat(d3.format('.02f'));
        chart.yAxis
            .tickFormat(d3.format('.02f'))
            .axisLabelDistance(20);

        /*
        chart.tooltipContent(function(key, x, y, e, graph) {
            return '<h3>GSM' + e.point.id + '</h3>';
        });

        if ("onClick" in params) {
            chart.scatter.dispatch.on("elementClick", params.onClick);
        }
        */
        return chart;
    },
    bar: function(o) {
        var chart = nv.models.discreteBarChart()
            .x(function(d) { return d[0] })
            .y(function(d) { return d[1] })
            .staggerLabels(true)    
            .showValues(true)       
            .transitionDuration(350)
            ;

        /*
        chart.tooltipContent(function(key, x, y, e, graph) {
            return '<h3> n = ' + e.point.Count + '</h3>';
        });
        */

        //chart.yAxis.axisLabelDistance(30);
        return chart;
    }
};

$(function() {
    $("div.plot").each(function() {
        plot.initialize($(this));
    });
});

    /*
        var div = $(this);
        var uuid = div.attr("uuid");
        $.post("/ajax/plot", {"uuid": uuid}, 
            function(o) {
                var chart = nv.models.scatterChart()
                    .color(d3.scale.category10().range());

                chart.tooltipContent(function(key, x, y, e, graph) {
                    return '<h3>GSM' + e.point.id + '</h3>';
                });

                if ("onClick" in params) {
                    chart.scatter.dispatch.on("elementClick", params.onClick);
                }

                chart.xAxis
                    .tickFormat(d3.format('.02f'))
                    .axisLabel(o["x-label"]);
                chart.yAxis
                    .tickFormat(d3.format('.02f'))
                    .axisLabelDistance(20)
                    .axisLabel(o["y-label"]);

                d3.select(svg)
                      .datum(o.data)
                      .call(chart);
                nv.utils.windowResize(chart.update);
            }, "json");
    });
    */
