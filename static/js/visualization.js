function chart_bar(data, data_full) {
    var config = category_config(data);
    window.addEventListener("load",function(event) {
        var ctx = document.getElementById('myChart').getContext('2d');
        window.myBar = new Chart(ctx, config);
    }, false);

    category_buttons(data, data_full, config);
}

function chart_bar_d3(data) {
    var parseDate = d3.timeParse("%b %Y");

    var n = data.names.length,
        m = data.dates.length,
        seriesNames = data.names,
        dates = data.dates.map(d => parseDate(d)),
        data = data.data;

    // console.log(data);
    var stack = d3.stack();//,
        // data = d3.range(n).map(function() { return bumpLayer(m, .1); });
    // console.log(data);

    var formatPercent = d3.format(".0%");
    var formatNumber = d3.format("");

    // transpose data
    data = data[0].map(function(col, i) {
        return data.map(function(row) {
            return row[i]
        })
    });

    var layers = stack.keys(d3.range(n))(data),
        yStackMax = d3.max(layers, function(layer) { return d3.max(layer, function(d) { return d[1]; }); }),
        yGroupMax = d3.max(layers, function(layer) { return d3.max(layer, function(d) { return d[1] - d[0]; }); });

    var margin = {top: 100, right: 20, bottom: 140, left: 35},
        containerWidth = document.querySelector(".js-stacked-chart-container").clientWidth,
        width = containerWidth - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    var margin2 = {top: margin.top + height + 20, right: 20, bottom: 20, left: 35},
        height2 = margin.bottom - (margin2.top - margin.top - height) - margin2.bottom;

    var num_look = 12,
        padding = 10;

    var x = d3.scaleTime()
        .domain([dates[m-num_look], dates[m-1]])
        .range([margin.left, width-margin.right-25]);

    var x2 = d3.scaleTime()
        .domain([dates[0], dates[m-1]])
        .range([margin.left, width-margin.right]);

    var y = d3.scaleLinear()
        .domain([0, yStackMax])
        .rangeRound([height, 0]);

    var y2 = d3.scaleLinear()
        .domain([0, yStackMax])
        .rangeRound([height2, 0]);

    var color = d3.scaleLinear()
        .domain([0, n-1])
        .range(["#80b6f4", "#f49080"]);

    var xAxis = d3.axisBottom()
        .scale(x)
        .tickSize(0)
        .tickPadding(6);

    var yAxis = d3.axisLeft()
        .scale(y)
        .tickSize(2)
        .tickPadding(6);
    var yAxisR = d3.axisRight()
        .scale(y)
        .tickSize(width-20)
        .tickPadding(6);

    var xAxis2 = d3.axisBottom()
        .scale(x2)
        .tickSize(0)
        .tickPadding(6);

    var brush = d3.brushX()
        .extent([[0, 0], [width, height2]])
        .on("brush", brushed);

    // var zoom = d3.zoom()
    //     .scaleExtent([1, Infinity])
    //     .translateExtent([[margin.left, margin.top], [width - margin.right, height - margin.top]])
    //     .extent([[margin.left, margin.top], [width - margin.right, height - margin.top]])
    //     .on("zoom", zoomed);

    var main_svg = d3.select(".js-stacked-chart")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    main_svg.append("g")
            .attr("class",  "js-stacked-chart-up")
            .attr("width", width - margin.left - margin.right)
            .attr("height", height - margin.top - margin.bottom)
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    // main_svg.append('rect')
    //     .attr("class", "zoom")
    //     .attr("width", width)
    //     .attr("height", height)
    //     .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    //     .call(zoom);

    main_svg.append("g")
            .attr("class",  "js-stacked-chart-down brush")
            .attr("width", width - margin.left - margin.right)
            .attr("height", height - margin.top - margin.bottom)
            .attr("transform", "translate(" + margin2.left + "," + margin2.top + ")")
          .call(brush)
          .call(brush.move, [x2(x.domain()[0]), x2(x.domain()[1])]);


    var svg = d3.select(".js-stacked-chart-up"),
        svg_map = d3.select(".js-stacked-chart-down");

    layers.forEach((l, i) => l.forEach((d, j) => {d.date = dates[j]; d.key = i}));

    var layer = svg.selectAll(".layer")
        .data(layers)
      .enter().append("g")
        .attr("class", "layer")
        .attr("id", function(d) { return d.key; })
        .style("fill", function(d, i) { return color(i); });

    var rect = layer.selectAll(".rect")
        .data(function(d) { return d; })
      .enter().append("rect")
        .attr("x", function(d) { return x(d.date)-width/num_look/2; })
        .attr("y", height)
        .attr("width", Math.max(width/num_look-padding,2))
        .attr("height", 0);

    rect.transition()
        .delay(function(d, i) {return 0; })
        .attr("y", function(d) { return y(d[1]); })
        .attr("height", function (d, i) {
                    if (d.date < x.domain()[0] || d.date > x.domain()[1]) {
                        return 0;
                    }
                    else
                        return y(d[0]) - y(d[1]);
                });

    var xAxisG = svg.append("g")
        .attr("class", "x-axis axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    svg.append("g")
        .attr("class", "y-axis axis")
        .attr("transform", "translate(" + 0 + ",0)")
        .style("font-size", "10px")
        .call(yAxis);

    svg.append("g")
        .attr("class", "y-axis axis r")
        .attr("transform", "translate(" + 0 + ",0)")
        .style("font-size", "10px")
        .call(yAxisR);

    svg_map.append("g")
        .attr("class", "x-axis axis")
        .attr("transform", "translate(0," + height2 + ")")
        .call(xAxis2);

    var layer_map = svg_map.selectAll(".layer")
        .data(layers)
      .enter().append("g")
        .attr("class", "layer")
        .attr("id", function(d) { return d.key; })
        .style("fill", function(d, i) { return color(i); });

    var rect_map = layer_map.selectAll("rect")
        .data(function(d) { return d; })
      .enter().append("rect")
        .attr("x", function(d) { return x2(d.date)-width/m/2; })
        .attr("y", height2)
        .attr("width", Math.max(width/m, 1))
        .attr("height", 0);

    rect_map.transition()
        .delay(function(d, i) {return i * 10; })
        .attr("y", function(d) { return y2(d[1]); })
        .attr("height", function(d) { return y2(d[0]) - y2(d[1]); });


    d3.selectAll("input").on("change", change);

    change_value = 'stacked';

    function change() {
        if (this.value === "grouped") {
            transitionGrouped();
            change_value = 'grouped';
        }
        else if (this.value === "stacked") {
            transitionStacked();
            change_value = 'stacked';
        }
        else if (this.value === "percent") {
            transitionPercent();
            change_value = 'percent';
        }
    }

    function transitionGrouped() {
        y.domain([0, yGroupMax]);
        y2.domain([0, yGroupMax]);

        rect.transition()
            .duration(400)
            .delay(function(d, i) { return 0; })
            .attr("x", function(d, i) { return x(d.date) + width/num_look / n * parseInt(d.key) - width/num_look/2; })
            .attr("width", Math.max(width/num_look/n - padding/2, 2))
        .transition()
            .attr("y", function(d) { return height - (y(d[0]) - y(d[1])); })
            .attr("height", function (d, i) {
                    if (d.date < x.domain()[0] || d.date > x.domain()[1]) {
                        return 0;
                    }
                    else
                        return y(d[0]) - y(d[1]);
                });

        rect_map.transition()
            .duration(400)
            .delay(function(d, i) { return 0; })
            .attr("x", function(d, i, j) { return x2(dates[i]) + width/m / n * d.key - width/m/2; })
            .attr("width", Math.max(width/m/n-padding, 1))
        .transition()
            .attr("y", function(d) { return height2 - (y2(d[0]) - y2(d[1])); })
            .attr("height", function(d) { return y2(d[0]) - y2(d[1]); });

        yAxis.tickFormat(formatNumber);
        yAxisR.tickFormat(formatNumber);
        svg.selectAll(".y-axis.axis").transition()
            .delay(200)
            .duration(200)
            .call(yAxis);

        svg.selectAll(".y-axis.axis.r").transition()
            .delay(200)
            .duration(200)
            .call(yAxisR)
    };

    function transitionStacked() {
        y.domain([0, yStackMax]);
        y2.domain([0, yStackMax]);

        rect.transition()
            .duration(400)
            .delay(function(d, i) { return 0; })
            .attr("y", function(d) { return y(d[1]); })
            .attr("height", function (d, i) {
                    if (d.date < x.domain()[0] || d.date > x.domain()[1]) {
                        return 0;
                    }
                    else
                        return y(d[0]) - y(d[1]);
                })
        .transition()
            .attr("x", function(d, i) { return x(d.date) - width/num_look/2; })
            .attr("width", Math.max(width/num_look - padding, 2));
        rect_map.transition()
            .duration(400)
            .delay(function(d, i) { return 0; })
            .attr("y", function(d) { return y2(d[1]); })
            .attr("height", function(d) { return y2(d[0]) - y2(d[1]); })
        .transition()
            .attr("x", function(d, i) { return x2(d.date); })
            .attr("width", Math.max(width/m - padding, 1));

        yAxis.tickFormat(formatNumber);
        yAxisR.tickFormat(formatNumber);
        svg.selectAll(".y-axis.axis").transition()
            .delay(200)
            .duration(200)
            .call(yAxis);

        svg.selectAll(".y-axis.axis.r").transition()
            .delay(200)
            .duration(200)
            .call(yAxisR);
    };

    function transitionPercent() {
        y.domain([0, 1]);
        y2.domain([0, 1]);

        rect.transition()
            .duration(400)
            .delay(function(d, i) { return 0; })
            .attr("y", function(d) {
                var total = d3.sum(d3.values(d.data));
                if (total == 0) return 0;
                return y(d[1] / total); })
            .attr("height", function(d, i) {
                    if (d.date < x.domain()[0] || d.date > x.domain()[1]) {
                        return 0;
                    }
                    else {
                        var total = d3.sum(d3.values(d.data));
                        if (total == 0) return 0;
                        return y(d[0] / total) - y(d[1] / total);
                    }})
        .transition()
            .attr("x", function(d, i) { return x(d.date) - width/num_look/2; })
            .attr("width", Math.max(width/num_look - padding, 2));
        rect_map.transition()
            .duration(400)
            .delay(function(d, i) { return 0; })
            .attr("y", function(d) {
                var total = d3.sum(d3.values(d.data));
                if (total == 0) return 0;
                return y2(d[1] / total); })
            .attr("height", function(d) {
                var total = d3.sum(d3.values(d.data));
                if (total == 0) return 0;
                return y2(d[0] / total) - y2(d[1] / total); })
        .transition()
            .attr("x", function(d, i) { return x2(d.date); })
            .attr("width", Math.max(width/m - padding, 1));

        yAxis.tickFormat(formatPercent);
        yAxisR.tickFormat(formatPercent);

        svg.selectAll(".y-axis.axis").transition()
            .delay(200)
            .duration(200)
            .call(yAxis);

        svg.selectAll(".y-axis.axis.r").transition()
            .delay(200)
            .duration(200)
            .call(yAxisR)
    };

    // Inspired by Lee Byron's test data generator.
    function bumpLayer(n, o) {

      function bump(a) {
        var x = 1 / (.1 + Math.random()),
            y = 2 * Math.random() - .5,
            z = 10 / (.1 + Math.random());
        for (var i = 0; i < n; i++) {
          var w = (i / n - y) * z;
          a[i] += x * Math.exp(-w * w);
        }
      }

      var a = [], i;
      for (i = 0; i < n; ++i) a[i] = o + o * Math.random();
      for (i = 0; i < 5; ++i) bump(a);

      return a.map(function(d, i) {

          return Math.floor(Math.random() * 2) * Math.max(0, d);
      });
    }


    function brushed(){
		if (!d3.event.sourceEvent) return; // Only transition after input.
  		if (!d3.event.selection) return; // Ignore empty selections.
		if(d3.event.sourceEvent && d3.event.sourceEvent.type === "zoom") return; // ignore brush-by-zoom
		var newInput = [];
		var brushArea = d3.event.selection;
		if(brushArea === null) brushArea = x2.range();

		dates.forEach(function(d){
			var pos = x2(d) + width/m/2;
			if (pos >= brushArea[0] && pos <= brushArea[1]){
			  newInput.push(d);
			}
		});

		x.domain([d3.min(newInput),d3.max(newInput)]);
		num_look = newInput.length;

		if (change_value == 'stacked') {
            rect.attr("x", function (d) { return x(d.date) - width/num_look/2; })
                .attr("y", function (d) { return y(d[1]); })
                .attr("width", Math.max(width/num_look - padding, 2))
                .attr("height", function (d, i) {
                    if (d.date < x.domain()[0] || d.date > x.domain()[1]) {
                        return 0;
                    }
                    else
                        return y(d[0]) - y(d[1]);
                });
        } else if (change_value == 'grouped') {
            rect.attr("x", function(d, i, j) {
                return x(d.date) + width/num_look / n * parseInt(d.key) - width/num_look/2;
            })
                .attr("width", Math.max(width/num_look/n - padding/2, 2))
                .attr("y", function(d) { return height - (y(d[0]) - y(d[1])); })
                .attr("height", function (d, i) {
                    if (d.date < x.domain()[0] || d.date > x.domain()[1]) {
                        return 0;
                    }
                    else
                        return y(d[0]) - y(d[1]);
                });
        } else if (change_value == 'percent') {
            rect.attr("y", function(d) {
                    var total = d3.sum(d3.values(d.data));
                    if (total == 0) return 0;
                    return y(d[1] / total); })
                .attr("height", function(d, i) {
                    if (d.date < x.domain()[0] || d.date > x.domain()[1]) {
                        return 0;
                    }
                    else {
                        var total = d3.sum(d3.values(d.data));
                        if (total == 0) return 0;
                        return y(d[0] / total) - y(d[1] / total);
                    }})
                .attr("x", function(d, i) { return x(d.date) - width/num_look/2; })
                .attr("width", Math.max(width/num_look - padding, 2));
        }

		xAxisG.call(xAxis);
        // var left=x2(x.domain()[0]);
		// var right = x2(x.domain()[1]) + Math.max(width/m - padding, 2);

		// brush.move([left,right]);

		 /*svg.select(".zoom").call(zoom.transform, d3.zoomIdentity
			.scale(width / (brushArea[1] - brushArea[0]))
			.translate(-brushArea[0], 0));*/
	}


    function zoomed() {
      if (d3.event.sourceEvent && d3.event.sourceEvent.type === "brush") return; // ignore zoom-by-brush
      //
      // x.range([margin.left, width - margin.right].map(d => d3.event.transform.applyX(d)));
      // console.log(x, x.range(), x.domain());
      // rect.attr("x", d => x(d[0]))
      //     .attr("width", x.bandwidth());
      // xAxisG.call(xAxis);
      // svg_map.select(".brush").call(brush.move, x.range().map(d3.event.transform.invertX, d3.event.transform));
    }

    var paddingBetweenLegendSeries = 5,
        legendSeriesBoxWidth = 15,
        legendSeriesBoxHeight = 15,
        legendSeriesHeight = legendSeriesBoxHeight + paddingBetweenLegendSeries,
        legendSeriesLabelX = -5,
        legendSeriesLabelY = legendSeriesBoxHeight / 2,
        legendMargin = 20,
        legendX = containerWidth / 2  - legendSeriesBoxWidth - legendMargin,
        legendY = - margin.top + legendMargin;

    var seriesClass = function (seriesName) { return "series-" + seriesName.toLowerCase(); };
    var legendSeriesClass = function (d) { return "clickable " + seriesClass(d); };

    var legendSeries = svg.append("g")
        .attr("class", "legend")
        .attr("transform", "translate(" + legendX + "," + legendY + ")")
        .selectAll("g").data(seriesNames.reverse())
            .enter().append("g")
                .attr("class", legendSeriesClass)
                .attr("transform", function (d, i) { return "translate(0," + (i * legendSeriesHeight) + ")"; });

    legendSeries.append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", legendSeriesBoxWidth)
        .attr("height", legendSeriesBoxHeight)
        .attr("fill", d => color(seriesNames.indexOf(d)));

    legendSeries.append("text")
        .attr("class", "series-label")
        .attr("x", legendSeriesLabelX)
        .attr("y", legendSeriesLabelY)
        .text(String);
}

function category_config(data) {
    return {
        type: 'bar',
        data: data,
        options: {
            title: {
                display: true,
                text: 'Categories'
            },
            tooltips: {
                mode: 'index',
                intersect: false
            },
            responsive: true,
            scales: {
                xAxes: [{
                    stacked: true,
                }],
                yAxes: [{
                    stacked: true
                }]
            },
            pan: {
                enabled: true,
                mode: 'x',
            },
            zoom: {
                enabled: true,
                mode: 'x',
            }
        }
    }
}

function category_buttons(data, data_full, config) {

    document.getElementById('addDataBar').addEventListener('click', function() {
        if (config.data.labels.length < data_full.labels.length) {
            idx = data_full.labels.length - config.data.labels.length - 1
            config.data.labels.unshift(data_full.labels[idx]);

            for (i = 0; i < data.datasets.length; i++) {
                config.data.datasets[i].data.unshift(data_full.datasets[i][idx]);
            }

            window.myBar.update();
        }
    });

    document.getElementById('removeDataBar').addEventListener('click', function() {
        if (config.data.labels.length > 0) {
            config.data.labels.shift(); // remove the label first

            config.data.datasets.forEach(function(dataset) {
                dataset.data.shift();
            });
            console.log(data_full)

            window.myBar.update();
        }
    });
}

function trend_config(data) {
    return {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            title: {
                display: false,
                text: 'Chart.js Line Chart'
            },
            tooltips: {
                mode: 'index',
                intersect: false,
            },
            hover: {
                mode: 'nearest',
                intersect: true
            },
            scales: {
                xAxes: [{
                    display: true
                }],
                yAxes: [{
                    display: true
                }]
            }
        }
    };
}

function trend_buttons(data, data_full, config) {
    var old_element = document.getElementById("addData");
    var new_element = old_element.cloneNode(true);
    old_element.parentNode.replaceChild(new_element, old_element);

    var old_element = document.getElementById("removeData");
    var new_element = old_element.cloneNode(true);
    old_element.parentNode.replaceChild(new_element, old_element);

    document.getElementById('addData').addEventListener('click', function() {
        if (config.data.labels.length < data_full.labels.length) {
            idx = data_full.labels.length - config.data.labels.length - 1;
            config.data.labels.unshift(data_full.labels[idx]);

            for (i = 0; i < data.datasets.length; i++) {
                config.data.datasets[i].data.unshift(data_full.datasets[i][idx]);
            }

            window.myLine.update();
        }
    });

    document.getElementById('removeData').addEventListener('click', function() {
        if (config.data.labels.length > 0) {
            config.data.labels.shift(); // remove the label first

            config.data.datasets.forEach(function(dataset) {
                dataset.data.shift();
            });

            window.myLine.update();
        }
    });
}

function trend_line(data, data_full) {
    var config = trend_config(data);

    window.addEventListener("load",function(event) {
        var ctx = document.getElementById('Trends').getContext('2d');
        window.myLine = new Chart(ctx, config);
    }, false);

    trend_buttons(data, data_full, config);

    document.getElementById("trend-button").addEventListener('click' , function() {
        var text = document.getElementById('trend-input').value;
        if (text.length != 0) {
            $.ajax({
                url: '/articles/api/v1/trend',
                type: 'post',
                data: {
                    'keywords_raw': text
                },
                dataType: 'json',
                success: function (data) {
                    data_full = data.data_full
                    data = data.data

                    var old_element = document.getElementById("Trends");
                    var new_element = old_element.cloneNode(true);
                    old_element.parentNode.replaceChild(new_element, old_element);

                    const ctx = new_element.getContext('2d');
                    var config = trend_config(data);

                    window.myLine = new Chart(ctx, config);
                    trend_buttons(data, data_full, config);
                }
            })
        }
    });

    document.getElementById("trend-input").addEventListener("keyup", function(event) {
      // Number 13 is the "Enter" key on the keyboard
      if (event.keyCode === 13) {
        // Cancel the default action, if needed
        event.preventDefault();
        // Trigger the button element with a click
        document.getElementById("trend-button").click();
      }
    });
}

