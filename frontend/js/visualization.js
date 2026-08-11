1// Visualization & Custom Chart Builder JS
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
  const selectColor = document.getElementById("builder-color-axis");
  const selectSize = document.getElementById("builder-size-axis");
  const selectChartType = document.getElementById("builder-chart-type");
  const selectAgg = document.getElementById("builder-aggregation");
  const selectPalette = document.getElementById("builder-palette");
  const chkLabels = document.getElementById("builder-show-labels");
  const chkSmooth = document.getElementById("builder-smooth-lines");
  const chkAuto = document.getElementById("builder-auto-update");
  
  const btnGenerate = document.getElementById("btn-generate-custom-chart");
  const btnDownload = document.getElementById("btn-download-chart");
  const btnExpand = document.getElementById("btn-expand-chart");

  if (!selectX || !selectY || !btnGenerate) return;

  try {
    const profile = await APIClient.request(`/api/analytics/${datasetId}/profile`);
    const columns = Object.keys(profile.columnProfiles || {});

    // Populate Column Dropdowns
    selectX.innerHTML = "<option value=''>-- Select X Axis --</option>";
    selectY.innerHTML = "<option value=''>-- Select Y Axis --</option>";
    if (selectColor) selectColor.innerHTML = "<option value=''>-- None (Single Series) --</option>";
    if (selectSize) selectSize.innerHTML = "<option value=''>-- None (Default Size) --</option>";

    columns.forEach(col => {
      const type = profile.columnProfiles[col].detectedType;

      const optX = document.createElement("option");
      optX.value = col;
      optX.textContent = `${col} (${type})`;
      selectX.appendChild(optX);

      const optY = document.createElement("option");
      optY.value = col;
      optY.textContent = `${col} (${type})`;
      selectY.appendChild(optY);

      if (selectColor) {
        const optC = document.createElement("option");
        optC.value = col;
        optC.textContent = `${col} (${type})`;
        selectColor.appendChild(optC);
      }

      if (selectSize) {
        const optS = document.createElement("option");
        optS.value = col;
        optS.textContent = `${col} (${type})`;
        selectSize.appendChild(optS);
      }
    });

    if (columns.length >= 1) selectX.value = columns[0];
    if (columns.length >= 2) selectY.value = columns[1];
    if (columns.length >= 3 && selectColor) selectColor.value = "";

    // Sync visual chart pills with select box
    const pills = document.querySelectorAll(".chart-pill");
    pills.forEach(pill => {
      pill.addEventListener("click", () => {
        pills.forEach(p => p.classList.remove("active"));
        pill.classList.add("active");

        const targetType = pill.getAttribute("data-type");
        if (selectChartType) selectChartType.value = targetType;

        if (!chkAuto || chkAuto.checked) {
          generateCustomPlot(datasetId);
        }
      });
    });

    if (selectChartType) {
      selectChartType.addEventListener("change", () => {
        const val = selectChartType.value;
        pills.forEach(p => {
          if (p.getAttribute("data-type") === val) p.classList.add("active");
          else p.classList.remove("active");
        });
        if (!chkAuto || chkAuto.checked) generateCustomPlot(datasetId);
      });
    }

    // Auto update listener on control changes
    const autoControls = [selectX, selectY, selectColor, selectSize, selectAgg, selectPalette, chkLabels, chkSmooth];
    autoControls.forEach(ctrl => {
      if (!ctrl) return;
      ctrl.addEventListener("change", () => {
        if (!chkAuto || chkAuto.checked) {
          generateCustomPlot(datasetId);
        }
      });
    });

    btnGenerate.addEventListener("click", () => generateCustomPlot(datasetId));

    if (btnDownload) {
      btnDownload.addEventListener("click", () => {
        const canvas = document.getElementById("custom-chart-canvas");
        if (canvas && canvas.data) {
          Plotly.downloadImage(canvas, { format: "png", width: 1200, height: 700, filename: "datalens_custom_chart" });
        }
      });
    }

    if (btnExpand) {
      btnExpand.addEventListener("click", () => {
        const canvas = document.getElementById("custom-chart-canvas");
        if (canvas && canvas.data) {
          const win = window.open("", "_blank");
          win.document.write(`
            <html>
              <head><title>Fullscreen View — DataLens Chart</title><script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script></head>
              <body style="margin:0; background:#0f172a; display:flex; align-items:center; justify-content:center; height:100vh;">
                <div id="full-canvas" style="width:95vw; height:90vh;"></div>
                <script>
                  Plotly.newPlot("full-canvas", ${JSON.stringify(canvas.data)}, ${JSON.stringify(canvas.layout)}, {responsive: true});
                </script>
              </body>
            </html>
          `);
        }
      });
    }

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
  const color = document.getElementById("builder-color-axis")?.value || "";
  const size = document.getElementById("builder-size-axis")?.value || "";
  const aggregation = document.getElementById("builder-aggregation")?.value || "none";
  const palette = document.getElementById("builder-palette")?.value || "indigo";
  const showLabels = document.getElementById("builder-show-labels")?.checked || false;
  const smoothLines = document.getElementById("builder-smooth-lines")?.checked || false;

  try {
    const chartData = await APIClient.request("/api/visualizations/generate", {
      method: "POST",
      body: JSON.stringify({
        datasetId,
        chartType,
        xAxis,
        yAxis,
        color,
        size,
        aggregation,
        palette,
        showLabels,
        smoothLines
      })
    });

    const canvas = document.getElementById("custom-chart-canvas");
    if (canvas) {
      Plotly.newPlot(canvas, chartData.plotlyData.data, chartData.plotlyData.layout, { responsive: true, displayModeBar: true });
    }
  } catch (err) {
    console.error("Error generating custom chart", err);
  }
}
