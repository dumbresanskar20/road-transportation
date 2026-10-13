/**
 * Analytics and Dashboard Visualizations with Chart.js
 */

document.addEventListener('DOMContentLoaded', function () {
    // Check if analytics container exists
    const analyticsContainer = document.getElementById('analyticsChartsContainer');
    if (!analyticsContainer) return;

    fetch('/api/analytics')
        .then(response => response.json())
        .then(data => {
            if (data.total_records === 0) {
                // Empty state handled in HTML
                return;
            }
            renderCharts(data);
        })
        .catch(err => {
            console.error('Error loading analytics data:', err);
        });

    function renderCharts(data) {
        // Palette
        const teal = '#0d9488';
        const navy = '#1e293b';
        const amber = '#d97706';
        const red = '#dc2626';
        const blue = '#2563eb';
        const cyan = '#06b6d4';
        const gray = '#94a3b8';

        // 1. Categories Distribution (Doughnut)
        const catCanvas = document.getElementById('categoryChart');
        if (catCanvas && Object.keys(data.category_distribution).length > 0) {
            const labels = Object.keys(data.category_distribution);
            const values = Object.values(data.category_distribution);

            new Chart(catCanvas, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: [teal, navy, amber, red, blue, cyan, gray],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }

        // 2. Priority Distribution (Pie)
        const prioCanvas = document.getElementById('priorityChart');
        if (prioCanvas && Object.keys(data.priority_distribution).length > 0) {
            const labels = Object.keys(data.priority_distribution);
            const values = Object.values(data.priority_distribution);
            const colorMap = {
                'High': '#dc2626',
                'Medium': '#d97706',
                'Low': '#0284c7',
                'Neutral': '#64748b'
            };

            new Chart(prioCanvas, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: labels.map(l => colorMap[l] || teal),
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }

        // 3. Top Activated Rules (Horizontal Bar)
        const rulesCanvas = document.getElementById('topRulesChart');
        if (rulesCanvas && data.top_rules.length > 0) {
            new Chart(rulesCanvas, {
                type: 'bar',
                data: {
                    labels: data.top_rules.map(r => r.rule_id),
                    datasets: [{
                        label: 'Activation Count',
                        data: data.top_rules.map(r => r.count),
                        backgroundColor: teal,
                        borderRadius: 6
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: { precision: 0 }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        // 4. Assessments Timeline (Line)
        const timeCanvas = document.getElementById('timelineChart');
        if (timeCanvas && data.timeline.length > 0) {
            new Chart(timeCanvas, {
                type: 'line',
                data: {
                    labels: data.timeline.map(t => t.date),
                    datasets: [{
                        label: 'Assessments',
                        data: data.timeline.map(t => t.count),
                        borderColor: teal,
                        backgroundColor: 'rgba(13, 148, 136, 0.1)',
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: teal,
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 }
                        }
                    }
                }
            });
        }

        // 5. Traffic Conditions (Bar)
        const trafficCanvas = document.getElementById('trafficDistChart');
        if (trafficCanvas && Object.keys(data.traffic_distribution).length > 0) {
            new Chart(trafficCanvas, {
                type: 'bar',
                data: {
                    labels: Object.keys(data.traffic_distribution),
                    datasets: [{
                        label: 'Assessments',
                        data: Object.values(data.traffic_distribution),
                        backgroundColor: [blue, amber, red],
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        // 6. Weather Conditions (Bar)
        const weatherCanvas = document.getElementById('weatherDistChart');
        if (weatherCanvas && Object.keys(data.weather_distribution).length > 0) {
            new Chart(weatherCanvas, {
                type: 'bar',
                data: {
                    labels: Object.keys(data.weather_distribution),
                    datasets: [{
                        label: 'Assessments',
                        data: Object.values(data.weather_distribution),
                        backgroundColor: [cyan, blue, navy],
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    }
});
