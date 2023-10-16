const ctx = document.getElementById("dailyChart");

Chart.defaults.backgroundColor = "rgba(255, 255, 255, 0.2)";
Chart.defaults.borderColor = "rgba(255, 255, 255, 0.2)";
Chart.defaults.color = "#FFF";

console.log(daily_data);
let labels = daily_data.map(([label, _]) => label);
let counts = daily_data.map(([_, count]) => count);
new Chart(ctx, {
  type: "line",
  data: {
    labels: labels,
    datasets: [
      {
        label: "daily active users",
        data: counts,
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
