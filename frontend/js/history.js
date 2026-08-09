// History & Dataset Management JS
document.addEventListener("DOMContentLoaded", async () => {
  loadDatasetHistory();
});

async function loadDatasetHistory() {
  const container = document.getElementById("history-datasets-table-body");
  if (!container) return;

  try {
    const datasets = await APIClient.request("/api/datasets");
    container.innerHTML = "";

    if (!datasets || datasets.length === 0) {
      container.innerHTML = "<tr><td colspan='7'>No datasets uploaded yet.</td></tr>";
      return;
    }

    datasets.forEach(ds => {
      const tr = document.createElement("tr");
      const isCurrent = (ds.id === APIClient.getActiveDatasetId());
      const dateStr = ds.createdAt || ds.uploadedAt ? new Date(ds.createdAt || ds.uploadedAt).toLocaleDateString() : "Just now";
      const qScore = ds.qualityScore || 95;

      tr.innerHTML = `
        <td><strong>${ds.name}</strong> ${isCurrent ? '<span class="btn btn-sm btn-primary">Active</span>' : ''}</td>
        <td>${(ds.fileCategory || 'tabular').toUpperCase()} (${(ds.fileType || 'csv').toUpperCase()})</td>
        <td>${(ds.rows || 0).toLocaleString()}</td>
        <td>${ds.columns || 0}</td>
        <td><strong style="color:${qScore >= 80 ? 'var(--accent-secondary)' : 'var(--accent-warning)'}">${qScore}/100</strong></td>
        <td>${dateStr}</td>
        <td>
          <button class="btn btn-sm btn-secondary" onclick="setActiveAndNavigate('${ds.id}')">Analyze</button>
          <button class="btn btn-sm btn-danger" onclick="confirmDeleteDataset('${ds.id}', '${ds.name}')">Delete</button>
        </td>
      `;
      container.appendChild(tr);
    });
  } catch (err) {
    console.error("Error loading history", err);
  }
}

function setActiveAndNavigate(id) {
  APIClient.setActiveDatasetId(id);
  window.location.href = "dashboard.html";
}

async function confirmDeleteDataset(id, name) {
  if (confirm(`Are you sure you want to delete dataset '${name}'? This action cannot be undone.`)) {
    try {
      await APIClient.request(`/api/datasets/${id}`, { method: "DELETE" });
      APIClient.showToast("Dataset deleted successfully.", "success");
      loadDatasetHistory();
    } catch (err) {
      console.error("Delete dataset error", err);
    }
  }
}
