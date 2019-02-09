function chart_bar(data) {
    window.addEventListener("load",function(event) {
        var ctx = document.getElementById('myChart').getContext('2d');
        window.myBar = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                title: {
                    display: true,
                    text: 'Chart.js Bar Chart - Stacked'
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
                }
            }
        });
    }, false);
}

function trend_line(data, data_full) {
    var config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            title: {
                display: true,
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

    window.addEventListener("load",function(event) {
        var ctx = document.getElementById('myTrend').getContext('2d');
        window.myLine = new Chart(ctx, config);
    }, false);

    document.getElementById('addData').addEventListener('click', function() {
        if (config.data.labels.length < data_full.labels.length) {
            idx = data_full.labels.length - config.data.labels.length - 1
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
