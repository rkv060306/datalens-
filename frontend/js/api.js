// DataLens Unified API Client with Dynamic Backend Host Resolution

function getApiBase() {
  const customUrl = localStorage.getItem("datalens_backend_url");
  if (customUrl && customUrl.trim()) {
    return customUrl.trim().replace(/\/$/, "");
  }
  // If hosted on GitHub Pages and no custom backend set
  if (window.location.hostname.includes("github.io")) {
    return "";
  }
  return ""; // Relative path when served directly by FastAPI
}

class APIClient {
  static getAuthToken() {
    return localStorage.getItem("datalens_token") || "";
  }

  static setAuthToken(token) {
    localStorage.setItem("datalens_token", token);
  }

  static getActiveDatasetId() {
    return localStorage.getItem("datalens_active_dataset_id") || "";
  }

  static setActiveDatasetId(id) {
    localStorage.setItem("datalens_active_dataset_id", id);
  }

  static getBackendUrl() {
    return getApiBase();
  }

  static setBackendUrl(url) {
    localStorage.setItem("datalens_backend_url", url);
  }

  static async ensureToken() {
    let token = this.getAuthToken();
    if (!token) {
      try {
        const apiBase = getApiBase();
        const res = await fetch(`${apiBase}/api/auth/guest-token`);
        if (res.ok) {
          const data = await res.json();
          this.setAuthToken(data.access_token);
          localStorage.setItem("datalens_user", JSON.stringify(data.user));
          token = data.access_token;
        }
      } catch (err) {
        console.warn("Could not reach backend guest token endpoint", err);
      }
    }
    return token;
  }

  static async request(endpoint, options = {}) {
    const apiBase = getApiBase();

    // Check if on GitHub Pages without configured backend URL
    if (window.location.hostname.includes("github.io") && !localStorage.getItem("datalens_backend_url")) {
      console.warn("Running static GitHub Pages build. Backend Python API is not attached to static GitHub Pages.");
    }

    const token = await this.ensureToken();

    const headers = {
      ...options.headers,
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    try {
      const response = await fetch(`${apiBase}${endpoint}`, {
        ...options,
        headers,
      });

      if (response.status === 401) {
        localStorage.removeItem("datalens_token");
        const newToken = await this.ensureToken();
        headers["Authorization"] = `Bearer ${newToken}`;
        const retryRes = await fetch(`${apiBase}${endpoint}`, { ...options, headers });
        if (!retryRes.ok) {
          const errData = await retryRes.json().catch(() => ({}));
          throw new Error(errData.detail || "API request failed");
        }
        return await retryRes.json();
      }

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server Error (${response.status})`);
      }

      return await response.json();
    } catch (error) {
      if (window.location.hostname.includes("github.io") && !localStorage.getItem("datalens_backend_url")) {
        APIClient.showToast("GitHub Pages only hosts static files. Deploy Python backend on Render/Railway to enable API endpoints.", "error");
      } else {
        APIClient.showToast(error.message || "Network Request Failed", "error");
      }
      throw error;
    }
  }

  static showToast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 4000);
  }
}
