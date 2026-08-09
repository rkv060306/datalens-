// Visualization & Custom Chart Builder JS
document.addEventListener("DOMContentLoaded", async () => {
  const datasetId = APIClient.getActiveDatasetId();
  if (!datasetId) return;

  loadRecommendedCharts(datasetId);
  setupChartBuilder(datasetId);
});

async function loadRecommendedCharts(datasetId) {
  try {
    const recommendations = await APIClient.request(`/api/visualizations/${datasetId}/recommendations`);
    const container = document.getElementById("recommended-charts-container");
    if (!container) return;

    container.innerHTML = "";
    if (!recommendations || recommendations.length === 0) {
      container.innerHTML = "<p style='color:var(--text-muted)'>No auto chart recommendations for this dataset format.</p>";
      return;
    }

    recommendations.forEach((rec, idx) => {
      const card = document.createElement("div");
      card.className = "plotly-canvas-wrapper";
      const divId = `rec-chart-div-${idx}`;
      card.innerHTML = `<div id="${divId}" style="width:100%; height:400px;"></div>`;
      container.appendChild(card);

      setTimeout(() => {
        Plotly.newPlot(divId, rec.plotlyData.data, rec.plotlyData.layout, { responsive: true });
      }, 50);
    });
  } catch (err) {
    console.error("Error loading recommended charts", err);
  }
}

async function setupChartBuilder(datasetId) {
  const selectX = document.getElementById("builder-x-axis");
  const selectY = document.getElementById("builder-y-axis");
  const selectChartType = document.getElementById("builder-chart-type");
  const selectAgg = document.getElementById("builder-aggregation");
  const btnGenerate = document.getElementById("btn-generate-custom-chart");

  if (!selectX || !selectY || !btnGenerate) return;

  try {
    const profile = await APIClient.request(`/api/analytics/${datasetId}/profile`);
    const columns = Object.keys(profile.columnProfiles || {});

    selectX.innerHTML = "<option value=''>-- Select X Axis --</option>";
    selectY.innerHTML = "<option value=''>-- Select Y Axis --</option>";

    columns.forEach(col => {
      const optX = document.createElement("option");
      optX.value = col;
      optX.textContent = `${col} (${profile.columnProfiles[col].detectedType})`;
      selectX.appendChild(optX);

      const optY = document.createElement("option");
      optY.value = col;
      optY.textContent = `${col} (${profile.columnProfiles[col].detectedType})`;
      selectY.appendChild(optY);
    });

    if (columns.length >= 1) selectX.value = columns[0];
    if (columns.length >= 2) selectY.value = columns[1];

    btnGenerate.addEventListener("click", () => generateCustomPlot(datasetId));

    // Auto trigger first plot
    generateCustomPlot(datasetId);

  } catch (err) {
    console.error("Error setting up chart builder", err);
  }
}

async function generateCustomPlot(datasetId) {
  const chartType = document.getElementById("builder-chart-type")?.value || "bar";
  const xAxis = document.getElementById("builder-x-axis")?.value || "";
  const yAxis = document.getElementById("builder-y-axis")?.value || "";
  const aggregation = document.getElementById("builder-aggregation")?.value || "none";

  try {
    const chartData = await APIClient.request("/api/visualizations/generate", {
      method: "POST",
      body: JSON.stringify({
        datasetId,
        chartType,
        xAxis,
        yAxis,
        aggregation
      })
    });

    const canvas = document.getElementById("custom-chart-canvas");
    if (canvas) {
      Plotly.newPlot(canvas, chartData.plotlyData.data, chartData.plotlyData.layout, { responsive: true });
    }
  } catch (err) {
    console.error("Error generating custom chart", err);
  }
}
