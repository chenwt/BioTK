alert("hi");

var margin = {top: 20, right: 20, bottom: 30, left: 40},
    width = 960 - margin.left - margin.right,
    height = 500 - margin.top - margin.bottom;

var x = d3.scale.linear()
    .range([0, width]);

var y = d3.scale.linear()
    .range([height, 0]);

var color = d3.scale.category10();

var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom");

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");


var svg = d3.select("body").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
  .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


d3.json("/static/test.json", function(error, json) {
    var xk = "foo";
    var yk = "bar";

    alert("hi");
    var data = json;
    data.forEach(function(d) {
        d[xk] = +d[xk];
        d[yk] = +d[yk];
    });
    alert("hi");
    x.domain(d3.extent(data, function(d) { 
            return d[xk];
    })).nice();
    y.domain(d3.extent(data, function(d) { 
            return d[yk];
    })).nice();

    alert("hi");
    svg.selectAll(".dot")
      .data(data)
    .enter().append("circle")
      .attr("class", "dot")
      .attr("r", 3.5)
      .attr("cx", function(d) { return x(d[xk]; }))
      .attr("cy", function(d) { return y(d[yk]; }));
});
