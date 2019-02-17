function chart_bar(data, data_full) {
    var config = category_config(data);
    console.log(data)
    window.addEventListener("load",function(event) {
        var ctx = document.getElementById('myChart').getContext('2d');
        window.myBar = new Chart(ctx, config);
    }, false);

    category_buttons(data, data_full, config);


    // document.getElementById("trend-button").addEventListener('click' , function() {
    //     var text = document.getElementById('trend-input').value;
    //     if (text.length != 0) {
    //         $.ajax({
    //             url: '/articles/api/v1/trend',
    //             type: 'post',
    //             data: {
    //                 'keywords_raw': text
    //             },
    //             dataType: 'json',
    //             success: function (data) {
    //                 data_full = data.data_full
    //                 data = data.data
    //
    //                 var old_element = document.getElementById("Trends");
    //                 var new_element = old_element.cloneNode(true);
    //                 old_element.parentNode.replaceChild(new_element, old_element);
    //
    //                 const ctx = new_element.getContext('2d');
    //                 var config = trend_config(data);
    //
    //                 window.myLine = new Chart(ctx, config);
    //                 trend_buttons(data, data_full, config);
    //             }
    //         })
    //     }
    // })
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
            }
        }
    }
}

function category_buttons(data, data_full, config) {
    // var old_element = document.getElementById("addDataBar");
    // var new_element = old_element.cloneNode(true);
    // old_element.parentNode.replaceChild(new_element, old_element);
    //
    // var old_element = document.getElementById("removeDataBar");
    // var new_element = old_element.cloneNode(true);
    // old_element.parentNode.replaceChild(new_element, old_element);

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
