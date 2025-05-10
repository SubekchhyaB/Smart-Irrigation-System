let moistureLineGraph;
let lastMoistureValue = null; // To store the last received moisture value

// Function to create the line graph
function createMoistureLineGraph(ctxId, labels, data) {
    return new Chart(document.getElementById(ctxId), {
        type: 'line',
        data: {
            labels: labels,  // Initial time labels
            datasets: [{
                label: 'Moisture Level (%)',
                data: data,  // Initial data
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#28a745',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Moisture (%)',
                        color: '#2c3e50',
                        font: { size: 14 }
                    },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                    ticks: { color: '#2c3e50' }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time',
                        color: '#2c3e50',
                        font: { size: 14 }
                    },
                    grid: { display: false },
                    ticks: { color: '#2c3e50' }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#2c3e50', font: { size: 14 } }
                },
                tooltip: {
                    backgroundColor: '#2c3e50',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#28a745',
                    borderWidth: 1
                }
            }
        }
    });
}

// Function to update the live line graph with new data
function updateMoistureLineGraph(chart, newMoisture) {
    const timeLabel = new Date().toLocaleTimeString(); // Get current time as label

    // If new moisture value is different from the last value, update the graph
    if (newMoisture !== lastMoistureValue) {
        lastMoistureValue = newMoisture;  // Store the latest value

        // Add the new time label and moisture value to the graph
        chart.data.labels.push(timeLabel);
        chart.data.datasets[0].data.push(newMoisture);

        // Limit the number of points on the graph (optional, remove if you want to keep all)
        if (chart.data.labels.length > 10) {
            chart.data.labels.shift();  // Remove the oldest time label
            chart.data.datasets[0].data.shift();  // Remove the oldest data point
        }

        chart.update();
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const initialLabels = ['6 AM', '9 AM', '12 PM', '3 PM', '6 PM', '9 PM', '12 AM']; // Initial dummy labels
    const initialData = [30, 45, 60, 55, 50, 40, 35];  // Initial dummy data

    moistureLineGraph = createMoistureLineGraph('moistureLineGraph', initialLabels, initialData);

    // Regularly update the line graph every 2 seconds
    setInterval(() => {
        fetch('/api/latest')
            .then(res => res.json())
            .then(data => {
                if (data.moisture !== undefined) {
                    updateMoistureLineGraph(moistureLineGraph, data.moisture);
                }
            })
            .catch(err => console.error("Failed to fetch moisture data:", err));
    }, 500);
});

