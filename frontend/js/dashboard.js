// DataLens Interactive Analytics Dashboard Engine

let cachedProfile = null;
let cachedInsights = [];
let cachedRecommendations = [];
let activeAggregationMode = "mean"; // 'mean', 'sum', 'max', 'min', 'count'

document.addEventListener("DOMContentLoaded", async () => {
  let datasetId = APIClient.getActiveDatasetId();
  const datasetSelect = document.getElementById("active-dataset-select");

  try {
    const userDatasets = await APIClient.request("/api/datasets");
    if (datasetSelect) {
      datasetSelect.innerHTML = "";
      if (userDatasets.length === 0) {
        const samples = await APIClient.request("/api/datasets/samples");
        if (samples.length > 0) {
          const formData = new FormData();
          formData.append("fileName", samples[0].fileName);
          const autoDs = await APIClient.request("/api/datasets/samples/load", { method: "POST", body: formData });
          datasetId = autoDs.id;
          APIClient.setActiveDatasetId(datasetId);
          userDatasets.push(autoDs);
        }
      }

      userDatasets.forEach(ds => {
        const opt = document.createElement("option");
        opt.value = ds.id;
        opt.textContent = `${ds.name} (${ds.rows} rows, ${ds.columns} cols)`;
        if (ds.id === datasetId) opt.selected = true;
        datasetSelect.appendChild(opt);
      });

      datasetSelect.addEventListener("change", (e) => {
        APIClient.setActiveDatasetId(e.target.value);
        window.location.reload();
      });
    }
  } catch (e) {
    console.error("Error loading dataset selector", e);
  }

  if (!datasetId) return;

  setupInteractiveToolbar();
  setupKpiClickHandlers();
  await loadDashboardAnalytics(datasetId);

  // Listen for palette theme changes to re-theme Plotly charts
  window.addEventListener("datalensThemeChanged", () => {
    rethemePlotlyCharts();
  });
});

function setupInteractiveToolbar() {
  const aggBtns = document.querySelectorAll(".pill-btn[data-agg]");
  aggBtns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      aggBtns.forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      activeAggregationMode = e.target.getAttribute("data-agg");
      updateKpisByAggregationMode();
    });
  });

  const searchInput = document.getElementById("dashboard-search-input");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      filterDashboardContent(e.target.value.toLowerCase().trim());
    });
  }
}

function setupKpiClickHandlers() {
  const kpiCards = document.querySelectorAll(".kpi-card");
  kpiCards.forEach(card => {
    card.addEventListener("click", () => {
      openKpiDetailModal(card.id);
    });
  });
}

async function loadDashboardAnalytics(datasetId) {
  try {
    cachedProfile = await APIClient.request(`/api/analytics/${datasetId}/profile`);
    cachedInsights = await APIClient.request(`/api/analytics/${datasetId}/insights`);
    cachedRecommendations = await APIClient.request(`/api/visualizations/${datasetId}/recommendations`);

    updateKpisByAggregationMode();
    renderInsightsFeed(cachedInsights);
    renderRecommendedCharts(cachedRecommendations);
  } catch (err) {
    console.error("Error loading dashboard analytics", err);
  }
}

function updateKpisByAggregationMode() {
  if (!cachedProfile) return;

  const elemRows = document.getElementById("kpi-rows");
  const elemCols = document.getElementById("kpi-cols");
  const elemMissing = document.getElementById("kpi-missing");
  const elemMemory = document.getElementById("kpi-memory");
  const elemQualityNum = document.getElementById("quality-score-num");
  const elemQualityLabel = document.getElementById("quality-score-label");

  if (elemRows) elemRows.textContent = cachedProfile.rows ? cachedProfile.rows.toLocaleString() : "0";
  if (elemCols) elemCols.textContent = cachedProfile.columns || "0";
  if (elemMissing) elemMissing.textContent = `${cachedProfile.missingPercentage || 0}%`;
  if (elemMemory) elemMemory.textContent = `${cachedProfile.memoryUsageMB || 0} MB`;

  if (elemQualityNum) elemQualityNum.textContent = cachedProfile.qualityScore || "0";
  if (elemQualityLabel) elemQualityLabel.textContent = cachedProfile.qualityBreakdown?.status || "Good";

  const scoreCircle = document.getElementById("quality-score-circle");
  if (scoreCircle) {
    scoreCircle.style.setProperty("--score", cachedProfile.qualityScore || 0);
  }
}

function renderInsightsFeed(insights) {
  const insightsContainer = document.getElementById("dashboard-insights-feed");
  if (!insightsContainer) return;

  insightsContainer.innerHTML = "";
  if (insights && insights.length > 0) {
    insights.slice(0, 5).forEach(ins => {
      const item = document.createElement("div");
      item.className = `insight-card-item ${ins.type || 'info'}`;
      item.setAttribute("data-title", ins.title.toLowerCase());
      item.setAttribute("data-desc", ins.description.toLowerCase());
      item.innerHTML = `
        <div class="insight-header">
          <span class="insight-title">${ins.title}</span>
          ${ins.metric ? `<span class="btn btn-sm btn-secondary">${ins.metric}</span>` : ''}
        </div>
        <div class="insight-desc">${ins.description}</div>
      `;
      insightsContainer.appendChild(item);
    });
  } else {
    insightsContainer.innerHTML = "<p style='color:var(--text-muted)'>No key insights generated yet.</p>";
  }
}

function renderRecommendedCharts(recommendations) {
  const chartGrid = document.getElementById("dashboard-charts-grid");
  if (!chartGrid) return;

  chartGrid.innerHTML = "";
  if (recommendations && recommendations.length > 0) {
    recommendations.slice(0, 4).forEach((rec, idx) => {
      const wrapper = document.createElement("div");
      wrapper.className = "plotly-canvas-wrapper card";
      wrapper.style.padding = "16px";
      const containerId = `dash-chart-${idx}`;
      wrapper.innerHTML = `
        <div class="chart-card-header">
          <h4 style="font-size:15px; font-weight:700;">${rec.chartType.toUpperCase()} — ${rec.title || 'Data Trend'}</h4>
          <button class="chart-action-btn" onclick="openChartFullscreen('${containerId}', '${rec.title || 'Chart'}')">🔍 Expand</button>
        </div>
        <div id="${containerId}" style="width:100%; height:320px;"></div>
      `;
      chartGrid.appendChild(wrapper);

      setTimeout(() => {
        const layout = getThemedPlotlyLayout(rec.plotlyData.layout);
        Plotly.newPlot(containerId, rec.plotlyData.data, layout, { responsive: true, displayModeBar: false });
      }, 50);
    });
  } else {
    chartGrid.innerHTML = "<p style='color:var(--text-muted)'>No automatic chart recommendations for this dataset type.</p>";
  }
}

function getThemedPlotlyLayout(baseLayout = {}) {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark-obsidian";
  const paperColor = "rgba(0,0,0,0)";
  const plotColor = "rgba(0,0,0,0)";
  const fontColor = isDark ? "#f8fafc" : "#0f172a";
  const gridColor = isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)";

  return {
    ...baseLayout,
    paper_bgcolor: paperColor,
    plot_bgcolor: plotColor,
    font: { family: "Inter, sans-serif", color: fontColor, size: 12 },
    margin: { t: 30, r: 20, l: 40, b: 40 },
    xaxis: { ...baseLayout.xaxis, gridcolor: gridColor, zerolinecolor: gridColor },
    yaxis: { ...baseLayout.yaxis, gridcolor: gridColor, zerolinecolor: gridColor }
  };
}

function rethemePlotlyCharts() {
  if (cachedRecommendations && cachedRecommendations.length > 0) {
    cachedRecommendations.slice(0, 4).forEach((rec, idx) => {
      const containerId = `dash-chart-${idx}`;
      const elem = document.getElementById(containerId);
      if (elem && elem.data) {
        const newLayout = getThemedPlotlyLayout(rec.plotlyData.layout);
        Plotly.relayout(containerId, newLayout);
      }
    });
  }
}

function filterDashboardContent(query) {
  const items = document.querySelectorAll("#dashboard-insights-feed .insight-card-item");
  items.forEach(item => {
    const title = item.getAttribute("data-title") || "";
    const desc = item.getAttribute("data-desc") || "";
    if (title.includes(query) || desc.includes(query)) {
      item.style.display = "block";
    } else {
      item.style.display = "none";
    }
  });
}

function openKpiDetailModal(kpiCardId) {
  if (!cachedProfile) return;

  const modal = document.getElementById("kpi-detail-modal");
  const modalBody = document.getElementById("kpi-detail-body");
  if (!modal || !modalBody) return;

  let title = "Dataset KPI Breakdown";
  let content = "";

  if (kpiCardId === "kpi-card-rows") {
    title = "📊 Rows & Dataset Volume Breakdown";
    content = `
      <p><strong>Total Rows:</strong> ${cachedProfile.rows.toLocaleString()}</p>
      <p><strong>Total Columns:</strong> ${cachedProfile.columns}</p>
      <p><strong>Duplicate Rows:</strong> ${cachedProfile.duplicateRows.toLocaleString()}</p>
      <p><strong>Memory Footprint:</strong> ${cachedProfile.memoryUsageMB} MB</p>
    `;
  } else if (kpiCardId === "kpi-card-missing") {
    title = "⚠️ Missing Values & Quality Report";
    content = `
      <p><strong>Missing Cell Percentage:</strong> ${cachedProfile.missingPercentage}%</p>
      <p><strong>Total Missing Cells:</strong> ${cachedProfile.missingCells.toLocaleString()}</p>
      <p><strong>Quality Index Score:</strong> ${cachedProfile.qualityScore}/100 (${cachedProfile.qualityBreakdown?.status || 'Good'})</p>
    `;
  } else {
    title = "📋 Column Types Breakdown";
    const types = cachedProfile.columnTypesSummary || {};
    content = `
      <p><strong>Numeric Columns:</strong> ${types.numeric || 0}</p>
      <p><strong>Categorical Columns:</strong> ${types.categorical || 0}</p>
      <p><strong>Datetime Columns:</strong> ${types.datetime || 0}</p>
      <p><strong>Boolean Columns:</strong> ${types.boolean || 0}</p>
    `;
  }

  document.getElementById("kpi-modal-title").textContent = title;
  modalBody.innerHTML = content;
  modal.classList.add("active");
}

function closeKpiDetailModal() {
  const modal = document.getElementById("kpi-detail-modal");
  if (modal) modal.classList.remove("active");
}

function openChartFullscreen(containerId, title) {
  const elem = document.getElementById(containerId);
  if (!elem || !elem.data) return;

  const modal = document.getElementById("kpi-detail-modal");
  const modalBody = document.getElementById("kpi-detail-body");
  if (!modal || !modalBody) return;

  document.getElementById("kpi-modal-title").textContent = `📈 ${title}`;
  modalBody.innerHTML = `<div id="modal-fullscreen-chart" style="width:100%; height:450px;"></div>`;
  modal.classList.add("active");

  setTimeout(() => {
    Plotly.newPlot("modal-fullscreen-chart", elem.data, elem.layout, { responsive: true });
  }, 100);
}
