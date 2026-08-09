// DataLens Unified API Client with Instant Guest Auth Fallback

const API_BASE = ""; // Relative path to current server host

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

  static async ensureToken() {
    let token = this.getAuthToken();
    if (!token) {
      try {
        const res = await fetch(`${API_BASE}/api/auth/guest-token`);
        if (res.ok) {
          const data = await res.json();
          this.setAuthToken(data.access_token);
          localStorage.setItem("datalens_user", JSON.stringify(data.user));
          token = data.access_token;
        }
      } catch (err) {
        console.error("Failed to get guest token", err);
      }
    }
    return token;
  }

  static async request(endpoint, options = {}) {
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
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
      });

      if (response.status === 401) {
        // Token expired or invalid -> refresh guest token
        localStorage.removeItem("datalens_token");
        const newToken = await this.ensureToken();
        headers["Authorization"] = `Bearer ${newToken}`;
        const retryRes = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
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
      APIClient.showToast(error.message || "Network Request Failed", "error");
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
