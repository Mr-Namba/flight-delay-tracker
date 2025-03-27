document.addEventListener('DOMContentLoaded', function () {
    const startBtn = document.getElementById('startBtn');
    const endBtn = document.getElementById('endBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const resetBtn = document.getElementById('resetBtn');
    const reasonSelect = document.getElementById('reasonSelect');
    const totalMinutesElem = document.getElementById('totalMinutes');
    let delayChart;
    
    startBtn.addEventListener('click', function () {
        const reason = reasonSelect.value;
        fetch('/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ reason: reason })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                alert('Delay started!');
            }
        });
    });
    
    endBtn.addEventListener('click', function () {
        fetch('/end', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                alert(`Delay ended! Duration: ${data.duration_minutes.toFixed(2)} minutes`);
            }
        });
    });
    
    downloadBtn.addEventListener('click', function () {
        window.location.href = '/download';
    });
    
    resetBtn.addEventListener('click', function () {
        const password = prompt("Enter password to reset data:");
        if (password) {
            fetch('/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ password: password })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    alert(data.message);
                    updateChart();
                }
            });
        }
    });
    
    // Function to update chart and total duration
    function updateChart() {
        fetch('/stats')
            .then(response => response.json())
            .then(data => {
                const dailyStats = data.daily_stats;
                const totalDuration = data.total_duration_minutes;
                totalMinutesElem.textContent = totalDuration.toFixed(2);
                
                // Prepare data for chart
                const labels = Object.keys(dailyStats).sort();
                const reasons = ["out body", "out 1-dot battery", "out of 2 dot battery", "out of 3 dot battery"];
                const datasets = reasons.map(reason => {
                    return {
                        label: reason,
                        data: labels.map(label => dailyStats[label][reason] || 0),
                        fill: false,
                        borderWidth: 2
                    };
                });
                
                if (delayChart) {
                    delayChart.data.labels = labels;
                    delayChart.data.datasets.forEach((dataset, idx) => {
                        dataset.data = labels.map(label => dailyStats[label][reasons[idx]] || 0);
                    });
                    delayChart.update();
                } else {
                    const ctx = document.getElementById('delayChart').getContext('2d');
                    delayChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: datasets
                        },
                        options: {
                            responsive: true,
                            scales: {
                                x: {
                                    title: {
                                        display: true,
                                        text: 'Date'
                                    }
                                },
                                y: {
                                    title: {
                                        display: true,
                                        text: 'Delay Duration (minutes)'
                                    }
                                }
                            }
                        }
                    });
                }
            });
    }
    
    // Update chart every 10 seconds and on load
    setInterval(updateChart, 10000);
    updateChart();
});

