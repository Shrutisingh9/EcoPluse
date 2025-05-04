const ctx = document.getElementById('emissionsChart').getContext('2d');
    const emissionsChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        datasets: [{
          label: 'CO₂ Emissions (tons)',
          data: [1.4, 1.2, 0.8, 0.4, 0.2],
          backgroundColor: 'rgba(0, 201, 141, 0.2)',
          borderColor: '#00C98D',
          borderWidth: 3,
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 0.2
            }
          }
        }
      }
    });