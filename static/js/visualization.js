function chart_bar(data) {
    window.onload = function () {
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
    };
}