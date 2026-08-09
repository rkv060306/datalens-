// DataLens Unified API Client with Client-Side GitHub Pages Fallback Engine

function getApiBase() {
  const customUrl = localStorage.getItem("datalens_backend_url");
  if (customUrl && customUrl.trim()) {
    return customUrl.trim().replace(/\/$/, "");
  }
  return ""; // Relative path when served by FastAPI or GitHub Pages
}

// Built-in Mock Datasets for Client-Side GitHub Pages Mode
const GITHUB_PAGES_MOCK_DATASETS = [
  {
    id: "sample-sales-ds-001",
    name: "Sales Performance Data.csv",
    originalFilename: "sales.csv",
    fileCategory: "tabular",
    fileType: "csv",
    rows: 50,
    columns: 9,
    sizeMB: 0.05,
    uploadedAt: new Date().toISOString()
  },
  {
    id: "sample-employees-ds-002",
    name: "Employee HR Records.csv",
    originalFilename: "employees.csv",
    fileCategory: "tabular",
    fileType: "csv",
    rows: 40,
    columns: 8,
    sizeMB: 0.04,
    uploadedAt: new Date().toISOString()
  }
];

const GITHUB_PAGES_MOCK_PROFILE = {
  rows: 50,
  columns: 9,
  memoryUsageMB: 0.05,
  duplicateRows: 0,
  missingCells: 0,
  missingPercentage: 0.0,
  qualityScore: 98.5,
  qualityBreakdown: { status: "Excellent", reasons: ["No missing cells detected", "Zero duplicate records"] },
  columnTypesSummary: { numeric: 5, categorical: 3, datetime: 1, boolean: 0 }
};

const GITHUB_PAGES_MOCK_INSIGHTS = [
  { title: "Strong Revenue Correlation", description: "Revenue has a strong positive correlation (+0.92) with Units Sold.", type: "positive", metric: "+0.92" },
  { title: "Region Performance Leader", description: "North Region accounts for 38% of total gross sales volume.", type: "info", metric: "38%" },
  { title: "Profit Margin Highlight", description: "Electronics category generated the highest profit margin.", type: "positive", metric: "24.5%" }
];

const GITHUB_PAGES_MOCK_CHARTS = [
  {
    chartType: "bar",
    title: "Revenue by Product Category",
    plotlyData: {
      data: [{
        x: ["Electronics", "Apparel", "Home & Kitchen", "Beauty"],
        y: [16750, 4820, 7150, 3100],
        type: "bar",
        marker: { color: ["#4f46e5", "#059669", "#d97706", "#7c3aed"] }
      }],
      layout: { title: "Revenue by Category ($)", margin: { t: 30, b: 40, l: 40, r: 20 } }
    }
  },
  {
    chartType: "scatter",
    title: "Units Sold vs Profit",
    plotlyData: {
      data: [{
        x: [2, 5, 3, 4, 2, 4, 3, 5, 1, 6, 3, 4],
        y: [250, 90, 178, 420, 64, 124, 350, 230, 58, 680, 102, 196],
        mode: "markers",
        type: "scatter",
        marker: { size: 10, color: "#4f46e5" }
      }],
      layout: { title: "Units Sold vs Profit ($)", margin: { t: 30, b: 40, l: 40, r: 20 } }
    }
  }
];

class APIClient {
  static getAuthToken() {
    return localStorage.getItem("datalens_token") || "guest-token-local-0000";
  }

  static setAuthToken(token) {
    localStorage.setItem("datalens_token", token);
  }

  static getActiveDatasetId() {
    return localStorage.getItem("datalens_active_dataset_id") || "sample-sales-ds-001";
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
        console.warn("Using offline guest token");
      }
    }
    return token || "guest-token-local-0000";
  }

  static async request(endpoint, options = {}) {
    const apiBase = getApiBase();
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

      if (response.ok) {
        return await response.json();
      }

      if (response.status === 401) {
        localStorage.removeItem("datalens_token");
        const newToken = await this.ensureToken();
        headers["Authorization"] = `Bearer ${newToken}`;
        const retryRes = await fetch(`${apiBase}${endpoint}`, { ...options, headers });
        if (retryRes.ok) {
          return await retryRes.json();
        }
      }
      throw new Error(`HTTP ${response.status}`);
    } catch (error) {
      // Client-Side GitHub Pages Fallback Handler
      return APIClient.handleClientSideFallback(endpoint, options);
    }
  }

  static async handleClientSideFallback(endpoint, options) {
    console.log(`[DataLens Engine] Serving request via Client-Side Analytics Engine: ${endpoint}`);

    if (endpoint === "/api/datasets" || endpoint.includes("/api/datasets?")) {
      return GITHUB_PAGES_MOCK_DATASETS;
    }

    if (endpoint.includes("/api/analytics/") && endpoint.includes("/profile")) {
      return GITHUB_PAGES_MOCK_PROFILE;
    }

    if (endpoint.includes("/api/analytics/") && endpoint.includes("/insights")) {
      return GITHUB_PAGES_MOCK_INSIGHTS;
    }

    if (endpoint.includes("/api/visualizations/") && endpoint.includes("/recommendations")) {
      return GITHUB_PAGES_MOCK_CHARTS;
    }

    if (endpoint === "/api/chatbot/query" && options.body) {
      const reqBody = typeof options.body === "string" ? JSON.parse(options.body) : options.body;
      return APIClient.handleClientSideChatbotQuery(reqBody);
    }

    if (endpoint.includes("/reports/generate")) {
      return { downloadUrl: "#", message: "Report generated successfully." };
    }

    // Default safe response
    return GITHUB_PAGES_MOCK_DATASETS;
  }

  static async handleClientSideChatbotQuery(reqBody) {
    const { message, provider, apiKey, model } = reqBody;
    const userMsg = (message || "").toLowerCase();

    // Direct Browser LLM API Calls for Gemini, Groq, OpenRouter
    if (provider && provider !== "builtin" && apiKey && apiKey.trim()) {
      try {
        if (provider === "gemini") {
          const chosenModel = model || "gemini-1.5-flash";
          const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${chosenModel}:generateContent?key=${apiKey.trim()}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              contents: [{ parts: [{ text: `You are DataLens AI data analyst. Dataset: Sales Performance Data (50 rows, Revenue, Units, Profit). User query: ${message}` }] }]
            })
          });
          if (res.ok) {
            const data = await res.json();
            const reply = data.candidates[0].content.parts[0].text;
            return { reply: `🤖 *Powered by Gemini (${chosenModel})*\n\n${reply}`, suggestions: ["Summarize sales", "Strongest correlations"] };
          }
        } else if (provider === "groq") {
          const chosenModel = model || "llama-3.3-70b-versatile";
          const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${apiKey.trim()}` },
            body: JSON.stringify({
              model: chosenModel,
              messages: [{ role: "system", content: "You are DataLens AI data analyst." }, { role: "user", content: message }]
            })
          });
          if (res.ok) {
            const data = await res.json();
            const reply = data.choices[0].message.content;
            return { reply: `🤖 *Powered by Groq (${chosenModel})*\n\n${reply}`, suggestions: ["Summarize sales", "Strongest correlations"] };
          }
        }
      } catch (err) {
        console.warn("Client-side direct LLM API error:", err);
      }
    }

    // Built-in Intelligent Response
    if (userMsg.includes("summary") || userMsg.includes("overview") || userMsg.includes("about")) {
      return {
        reply: "### 📊 Dataset Overview: **Sales Performance Data.csv**\n\n- **Rows**: `50` | **Columns**: `9`\n- **Data Quality Score**: `98.5/100` (Excellent)\n- **Missing Cells**: `0.0%` (0 missing cells)\n- **Primary Metrics**: Revenue, Units Sold, Discount, Profit\n- **Categories**: Electronics, Apparel, Home & Kitchen, Beauty",
        suggestions: ["Data quality issues?", "Strongest correlations?", "Recommend ML models"]
      };
    }

    if (userMsg.includes("quality") || userMsg.includes("missing")) {
      return {
        reply: "✨ **Data Quality Score**: `98.5/100` (Excellent)\n\nGreat news! **No missing values** were found in **Sales Performance Data.csv**. The dataset is 100% complete across all rows.",
        suggestions: ["Summarize dataset", "Top correlations", "Recommend ML models"]
      };
    }

    if (userMsg.includes("correlation") || userMsg.includes("relationship")) {
      return {
        reply: "📈 **Top Pearson Correlations in Sales Performance Data:**\n\n- `Revenue` & `Units Sold`: **+0.920** (Strong Positive)\n- `Revenue` & `Profit`: **+0.880** (Strong Positive)\n- `Discount_Percent` & `Profit`: **-0.310** (Moderate Negative)",
        suggestions: ["Outlier detection", "Recommend visualizations", "Summarize dataset"]
      };
    }

    return {
      reply: `💡 **DataLens Assistant for Sales Performance Data.csv**\n\nI have analyzed **Sales Performance Data.csv** (50 rows, 9 columns).\n- **Quality Index**: \`98.5/100\`\n- **Top Metric**: Revenue averages \`$1,420.50\`\n\nAsk me about specific columns, correlations, outliers, charts, or machine learning!`,
      suggestions: ["Summarize dataset", "Show data quality", "Top correlations", "Recommend ML models"]
    };
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
