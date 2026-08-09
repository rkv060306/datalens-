// Insights, Correlation, Outliers & Machine Learning Module JS
document.addEventListener("DOMContentLoaded", async () => {
  const datasetId = APIClient.getActiveDatasetId();
  if (!datasetId) return;

  loadInsights(datasetId);
  loadCorrelationMatrix(datasetId);
  loadOutliers(datasetId);
  setupMLRunner(datasetId);
  loadMediaAnalytics(datasetId);
});

async function loadInsights(datasetId) {
  try {
    const insights = await APIClient.request(`/api/analytics/${datasetId}/insights`);
    const container = document.getElementById("insights-full-container");
    if (!container) return;

    container.innerHTML = "";
    if (!insights || insights.length === 0) {
      container.innerHTML = "<p style='color:var(--text-muted)'>No insights generated.</p>";
      return;
    }

    insights.forEach(ins => {
      const card = document.createElement("div");
      card.className = `card insight-card-item ${ins.type}`;
      card.style.marginBottom = "16px";
      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <h3 style="font-size:16px; font-weight:700;">${ins.title}</h3>
          <span class="btn btn-sm btn-secondary">${ins.category}</span>
        </div>
        <p style="font-size:14px; margin-bottom:6px;">${ins.description}</p>
        <p style="font-size:12px; color:var(--text-muted); font-style:italic;">Calculation detail: ${ins.explanation}</p>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Error loading insights", err);
  }
}

async function loadCorrelationMatrix(datasetId) {
  try {
    const corr = await APIClient.request(`/api/analytics/${datasetId}/correlation`);
    const container = document.getElementById("correlation-heatmap-container");
    if (!container) return;

    if (!corr || !corr.matrix || corr.matrix.length === 0) {
      container.innerHTML = `<p style='color:var(--text-muted)'>${corr.message || 'Correlation matrix requires numeric columns.'}</p>`;
      return;
    }

    Plotly.newPlot(container, [{
      z: corr.matrix,
      x: corr.columns,
      y: corr.columns,
      type: "heatmap",
      colorscale: "Viridis"
    }], {
      title: "Pearson Correlation Matrix",
      template: "plotly_dark"
    }, { responsive: true });

  } catch (err) {
    console.error("Error loading correlation matrix", err);
  }
}

async function loadOutliers(datasetId) {
  try {
    const outliers = await APIClient.request(`/api/analytics/${datasetId}/outliers`);
    const container = document.getElementById("outliers-list-container");
    if (!container) return;

    container.innerHTML = "";
    const cols = outliers.outlierColumns || {};
    if (Object.keys(cols).length === 0) {
      container.innerHTML = "<p style='color:var(--text-muted)'>No statistical outliers detected in numeric columns.</p>";
      return;
    }

    for (const [colName, info] of Object.entries(cols)) {
      const item = document.createElement("div");
      item.className = "card";
      item.style.marginBottom = "14px";
      item.innerHTML = `
        <h4>Outliers in <b>${colName}</b></h4>
        <p style="font-size:13px; color:var(--text-muted)">IQR Outliers: ${info.iqrOutlierCount} (${info.outlierPercentage}%) | Normal bounds: [${info.lowerBound} to ${info.upperBound}]</p>
        <p style="font-size:12px; margin-top:4px;">Sample outliers: ${info.sampleOutliers.join(', ')}</p>
      `;
      container.appendChild(item);
    }
  } catch (err) {
    console.error("Error loading outliers", err);
  }
}

async function setupMLRunner(datasetId) {
  const targetSelect = document.getElementById("ml-target-col");
  const btnRun = document.getElementById("btn-run-ml");
  const resultDiv = document.getElementById("ml-results-div");

  if (!targetSelect || !btnRun) return;

  try {
    const profile = await APIClient.request(`/api/analytics/${datasetId}/profile`);
    const cols = Object.keys(profile.columnProfiles || {});

    targetSelect.innerHTML = "";
    cols.forEach(c => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      targetSelect.appendChild(opt);
    });

    if (cols.length >= 1) targetSelect.value = cols[cols.length - 1];

    btnRun.addEventListener("click", async () => {
      const targetCol = targetSelect.value;
      const modelType = document.getElementById("ml-model-type")?.value || "linear_regression";
      const featureCols = cols.filter(c => c !== targetCol);

      APIClient.showToast("Training Machine Learning Model...", "info");

      try {
        const res = await APIClient.request(`/api/analytics/${datasetId}/ml`, {
          method: "POST",
          body: JSON.stringify({
            targetColumn: targetCol,
            featureColumns: featureCols,
            modelType: modelType
          })
        });

        if (!res.isSuitable) {
          resultDiv.innerHTML = `<div class="toast error"><span>${res.message}</span></div>`;
          return;
        }

        let metricsHtml = Object.entries(res.metrics || {})
          .map(([k, v]) => `<strong>${k}:</strong> ${v}`)
          .join(" | ");

        let importanceHtml = Object.entries(res.featureImportance || {})
          .map(([k, v]) => `<li>${k}: ${v}</li>`)
          .join("");

        resultDiv.innerHTML = `
          <div class="card" style="margin-top:16px;">
            <h3>🤖 Model Output: ${res.modelType}</h3>
            <p style="margin:8px 0;">${res.message}</p>
            <p style="background:var(--bg-dark); padding:10px; border-radius:var(--radius-sm); font-size:13px;">${metricsHtml}</p>
            ${importanceHtml ? `<h4 style="margin-top:12px;">Feature Importances / Coefficients:</h4><ul>${importanceHtml}</ul>` : ''}
          </div>
        `;

        APIClient.showToast("ML Model trained successfully!", "success");

      } catch (err) {
        console.error("ML Training error", err);
      }
    });

  } catch (err) {
    console.error("Error setting up ML runner", err);
  }
}

async function loadMediaAnalytics(datasetId) {
  const container = document.getElementById("media-analytics-container");
  if (!container) return;

  try {
    const res = await APIClient.request(`/api/analytics/media/${datasetId}`);
    if (res.error) {
      container.style.display = "none";
      return;
    }

    container.style.display = "block";
    container.innerHTML = `
      <div class="card">
        <h3>📹 ${res.mediaType} Media Analytics</h3>
        <p><strong>Dimensions:</strong> ${res.width} x ${res.height} px</p>
        ${res.brightness ? `<p><strong>Mean Brightness:</strong> ${res.brightness}</p>` : ''}
        ${res.contrast ? `<p><strong>Contrast Level:</strong> ${res.contrast}</p>` : ''}
        ${res.fps ? `<p><strong>Frame Rate:</strong> ${res.fps} FPS</p>` : ''}
        ${res.durationSeconds ? `<p><strong>Duration:</strong> ${res.durationSeconds} seconds</p>` : ''}
        ${res.ocrDetectedText ? `<p><strong>OCR Extracted Text:</strong> ${res.ocrDetectedText}</p>` : ''}
      </div>
    `;
  } catch (e) {
    // Non-media dataset, hide section
    container.style.display = "none";
  }
}
