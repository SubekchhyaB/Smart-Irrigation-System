let moistureGauge;

function createMoistureGauge(ctxId, value, label, color) {
    return new Chart(document.getElementById(ctxId), {
        type: 'doughnut',
        data: {
            labels: [label, ''],
            datasets: [{
                data: [value, 100 - value],
                backgroundColor: [color, '#e0e0e0'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false },
                title: {
                    display: true,
                    text: `${label}: ${value}%`,
                    font: { size: 18 }
                }
            }
        }
    });
}

function updateMoistureGauge(chart, newValue) {
    const safeValue = Math.min(100, Math.max(0, newValue)); // Clamp between 0–100
    chart.data.datasets[0].data[0] = safeValue;
    chart.data.datasets[0].data[1] = 100 - safeValue;
    chart.options.plugins.title.text = `Moisture: ${safeValue}%`;
    chart.update();
}

document.addEventListener("DOMContentLoaded", function () {
    moistureGauge = createMoistureGauge('humidityGauge', 0, 'Moisture', '#66bb6a');

    setInterval(() => {
        fetch('/api/latest')
            .then(res => res.json())
            .then(data => {
                if (data.moisture !== undefined) {
                    updateMoistureGauge(moistureGauge, data.moisture);
                }
            })
            .catch(err => console.error("Failed to fetch moisture data:", err));
    }, 500);
});

