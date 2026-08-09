// File Upload & Sample Dataset Module
document.addEventListener("DOMContentLoaded", () => {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const sampleContainer = document.getElementById("sample-datasets-container");

  // Load sample dataset list
  if (sampleContainer) {
    loadSampleDatasets(sampleContainer);
  }

  if (dropZone && fileInput) {
    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => {
      dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        handleFileUpload(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", (e) => {
      if (fileInput.files.length > 0) {
        handleFileUpload(fileInput.files[0]);
      }
    });
  }
});

async function handleFileUpload(file) {
  APIClient.showToast(`Analyzing ${file.name}...`, "info");

  // Read file client-side for GitHub Pages or static mode
  const reader = new FileReader();
  reader.onload = async (event) => {
    const text = event.target.result;
    if (text) {
      const customMeta = APIClient.registerClientSideDataset(file.name, text);
      if (customMeta) {
        APIClient.setActiveDatasetId(customMeta.id);
        APIClient.showToast(`Custom dataset '${file.name}' loaded & profiled!`, "success");
        setTimeout(() => {
          window.location.href = "dashboard.html";
        }, 600);
        return;
      }
    }
    
    // Fallback attempt to server backend if present
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await APIClient.request("/api/datasets/upload", {
        method: "POST",
        body: formData
      });
      APIClient.setActiveDatasetId(res.id);
      APIClient.showToast("Dataset uploaded and profiled successfully!", "success");
      setTimeout(() => {
        window.location.href = "dashboard.html";
      }, 600);
    } catch (err) {
      console.error("Upload error", err);
    }
  };

  reader.onerror = () => {
    APIClient.showToast("Failed to read selected file.", "error");
  };

  reader.readAsText(file);
}

async function loadSampleDatasets(container) {
  try {
    const samples = await APIClient.request("/api/datasets/samples");
    container.innerHTML = "";

    if (!samples || samples.length === 0) {
      container.innerHTML = "<p style='color:var(--text-muted)'>No sample datasets available.</p>";
      return;
    }

    samples.forEach(s => {
      const card = document.createElement("div");
      card.className = "sample-card";
      card.innerHTML = `
        <div class="sample-icon">📊</div>
        <div class="sample-title">${s.name}</div>
        <div style="font-size:12px; color:var(--text-muted)">Click to analyze instantly</div>
      `;
      card.addEventListener("click", () => loadSampleByName(s.fileName));
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Error loading sample datasets", err);
  }
}

async function loadSampleByName(fileName) {
  const formData = new FormData();
  formData.append("fileName", fileName);

  APIClient.showToast(`Loading sample dataset...`, "info");

  try {
    const res = await APIClient.request("/api/datasets/samples/load", {
      method: "POST",
      body: formData
    });

    APIClient.setActiveDatasetId(res.id);
    APIClient.showToast("Sample dataset loaded successfully!", "success");
    setTimeout(() => {
      window.location.href = "dashboard.html";
    }, 800);
  } catch (err) {
    console.error("Failed to load sample dataset", err);
  }
}
