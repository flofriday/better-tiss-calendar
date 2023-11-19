const ctx = document.getElementById("dailyChart");

Chart.defaults.backgroundColor = "rgba(255, 255, 255, 0.2)";
Chart.defaults.borderColor = "rgba(255, 255, 255, 0.2)";
Chart.defaults.color = "#FFF";

console.log(chart_data);
let labels = chart_data.map(([l, d, m, t]) => l);
let daily = chart_data.map(([l, d, m, t]) => d);
let monthly = chart_data.map(([l, d, m, t]) => m);
let total = chart_data.map(([l, d, m, t]) => t);
new Chart(ctx, {
  type: "line",
  data: {
    labels: labels,
    datasets: [
      {
        label: "daily",
        data: daily,
        borderWidth: 1,
      },
      {
        label: "montly",
        data: monthly,
        borderWidth: 1,
      },
      {
        label: "total",
        data: total,
        borderWidth: 1,
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
