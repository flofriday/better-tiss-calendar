let currentChart = null;

function drawStatisticsChart(displayData) {
  if (currentChart) currentChart.destroy();

  const ctx = document.getElementById("dailyChart");

  Chart.defaults.backgroundColor = "rgba(255, 255, 255, 0.2)";
  Chart.defaults.borderColor = "rgba(255, 255, 255, 0.2)";
  Chart.defaults.color = "#FFF";

  console.log(displayData);
  let labels = displayData.map(([l, d, m, t]) => l);
  let daily = displayData.map(([l, d, m, t]) => d);
  let monthly = displayData.map(([l, d, m, t]) => m);
  let total = displayData.map(([l, d, m, t]) => t);
  currentChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "daily",
          data: daily,
          borderWidth: 1,
          borderColor: "#a3c4f3",
          backgroundColor: "#a3c4f3",
        },
        {
          label: "montly",
          data: monthly,
          borderWidth: 1,
          borderColor: "#ffcfd2",
          backgroundColor: "#ffcfd2",
        },
        {
          label: "total",
          data: total,
          borderWidth: 1,
          borderColor: "#b9fbc0",
          backgroundColor: "#b9fbc0",
        },
      ],
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
        },
      },
      elements: {
        point: {
          radius: 2,
        },
      },
    },
  });
}

const lastMonthCheck = document.getElementById("last-month");
lastMonthCheck.addEventListener("change", render);

function render() {
  if (lastMonthCheck.checked) {
    // only last 30 days
    drawStatisticsChart(chart_data.slice(Math.max(chart_data.length - 30, 0)));
  } else {
    // original
    drawStatisticsChart(chart_data);
  }
}

render();
