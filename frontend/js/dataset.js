// Dataset Table Preview & Data Cleaning JS
let currentPage = 1;
let currentSearch = "";
let currentSortBy = "";
let currentSortOrder = "asc";

document.addEventListener("DOMContentLoaded", async () => {
  const datasetId = APIClient.getActiveDatasetId();
  if (!datasetId) return;

  loadDatasetTable(datasetId);

  const searchInput = document.getElementById("table-search-input");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      currentSearch = e.target.value;
      currentPage = 1;
      loadDatasetTable(datasetId);
    });
  }

  const prevBtn = document.getElementById("btn-prev-page");
  const nextBtn = document.getElementById("btn-next-page");

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage--;
        loadDatasetTable(datasetId);
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      currentPage++;
      loadDatasetTable(datasetId);
    });
  }

  const cleanBtn = document.getElementById("btn-open-clean-modal");
  if (cleanBtn) {
    cleanBtn.addEventListener("click", openCleanModal);
  }

  const applyCleanBtn = document.getElementById("btn-apply-cleaning");
  if (applyCleanBtn) {
    applyCleanBtn.addEventListener("click", applyDataCleaning);
  }
});

async function loadDatasetTable(datasetId) {
  try {
    const data = await APIClient.request(
      `/api/datasets/${datasetId}?page=${currentPage}&pageSize=25&search=${encodeURIComponent(currentSearch)}&sortBy=${currentSortBy}&sortOrder=${currentSortOrder}`
    );

    const ds = data.dataset;
    const preview = data.preview;

    const titleElem = document.getElementById("dataset-title");
    if (titleElem) titleElem.textContent = `${ds.name} — Data Preview (${ds.rows.toLocaleString()} rows, ${ds.columns} columns)`;

    const tableHead = document.getElementById("data-table-head");
    const tableBody = document.getElementById("data-table-body");
    const pageInfo = document.getElementById("page-info-span");

    if (!preview || !preview.columns) {
      if (tableBody) tableBody.innerHTML = "<tr><td colspan='10'>No tabular preview available for this dataset type.</td></tr>";
      return;
    }

    if (pageInfo) {
      pageInfo.textContent = `Page ${preview.page} of ${preview.totalPages} (${preview.totalRows.toLocaleString()} total matching rows)`;
    }

    // Render Table Header
    if (tableHead) {
      tableHead.innerHTML = `
        <tr>
          ${preview.columns.map(col => `
            <th onclick="sortTableColumn('${col}')" style="cursor:pointer;">
              ${col} ${currentSortBy === col ? (currentSortOrder === 'asc' ? '▲' : '▼') : ''}
            </th>
          `).join('')}
        </tr>
      `;
    }

    // Render Table Rows
    if (tableBody) {
      tableBody.innerHTML = preview.records.map(row => `
        <tr>
          ${preview.columns.map(col => `<td>${row[col] !== null ? row[col] : '<span style="color:var(--accent-danger)">N/A</span>'}</td>`).join('')}
        </tr>
      `).join('');
    }

  } catch (err) {
    console.error("Error loading dataset table", err);
  }
}

function sortTableColumn(col) {
  if (currentSortBy === col) {
    currentSortOrder = currentSortOrder === "asc" ? "desc" : "asc";
  } else {
    currentSortBy = col;
    currentSortOrder = "asc";
  }
  const datasetId = APIClient.getActiveDatasetId();
  loadDatasetTable(datasetId);
}

function openCleanModal() {
  const modal = document.getElementById("cleaning-modal");
  if (modal) modal.classList.add("active");
}

function closeCleanModal() {
  const modal = document.getElementById("cleaning-modal");
  if (modal) modal.classList.remove("active");
}

async function applyDataCleaning() {
  const datasetId = APIClient.getActiveDatasetId();
  const removeDuplicates = document.getElementById("clean-remove-duplicates")?.checked || false;
  const missingStrategySelect = document.getElementById("clean-missing-strategy")?.value || "mean";

  APIClient.showToast("Executing data cleaning operations...", "info");

  try {
    const res = await APIClient.request(`/api/datasets/${datasetId}/clean`, {
      method: "POST",
      body: JSON.stringify({
        removeDuplicates: removeDuplicates,
        missingStrategy: { "*": missingStrategySelect }
      })
    });

    closeCleanModal();
    APIClient.setActiveDatasetId(res.cleanedDataset.id);
    APIClient.showToast("Data cleaned successfully! New dataset created.", "success");
    setTimeout(() => window.location.reload(), 800);
  } catch (err) {
    console.error("Cleaning error", err);
  }
}
