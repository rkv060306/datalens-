/**
 * DataLens AI Chatbot Engine & Floating Assistant Drawer
 * Supports Built-in Analytics AI and free LLM models (Gemini, Groq, OpenRouter, HuggingFace) via API keys.
 */

(function () {
  const API_KEYS_STORAGE_KEY = "datalens_api_keys";
  let activeProvider = "builtin"; // 'builtin', 'gemini', 'groq', 'openrouter', 'huggingface'
  let activeModel = "";
  let messageHistory = [];

  function getSavedApiKeys() {
    try {
      return JSON.parse(localStorage.getItem(API_KEYS_STORAGE_KEY)) || {};
    } catch {
      return {};
    }
  }

  function saveApiKey(provider, key) {
    const keys = getSavedApiKeys();
    keys[provider] = key;
    localStorage.setItem(API_KEYS_STORAGE_KEY, JSON.stringify(keys));
  }

  function getApiKeyForProvider(provider) {
    return getSavedApiKeys()[provider] || "";
  }

  // Preset suggestion prompts
  const PRESET_SUGGESTIONS = [
    "📊 Summarize this dataset",
    "⚠️ Data quality issues & missing values",
    "🔥 Top correlations & dependencies",
    "🚨 Detect extreme outliers (IQR)",
    "🤖 Recommend ML models for prediction",
    "📈 Suggest best chart visualizations"
  ];

  document.addEventListener("DOMContentLoaded", () => {
    initMainChatbotPage();
    initFloatingChatDrawer();
  });

  // --- Main Chatbot Page Initialization ---
  function initMainChatbotPage() {
    const chatContainer = document.getElementById("main-chat-messages");
    if (!chatContainer) return; // Not on chatbot.html page

    const providerSelect = document.getElementById("ai-provider-select");
    const modelSelect = document.getElementById("ai-model-select");
    const apiKeyInput = document.getElementById("ai-api-key-input");
    const saveKeyBtn = document.getElementById("btn-save-api-key");
    const chatInput = document.getElementById("main-chat-input");
    const sendBtn = document.getElementById("main-chat-send");
    const chipsContainer = document.getElementById("main-chat-chips");
    const clearBtn = document.getElementById("btn-clear-chat");

    if (providerSelect) {
      providerSelect.addEventListener("change", (e) => {
        activeProvider = e.target.value;
        updateModelDropdownOptions(activeProvider, modelSelect);
        if (apiKeyInput) {
          apiKeyInput.value = getApiKeyForProvider(activeProvider);
        }
      });
      // Initial trigger
      updateModelDropdownOptions(providerSelect.value, modelSelect);
      if (apiKeyInput) apiKeyInput.value = getApiKeyForProvider(providerSelect.value);
    }

    if (saveKeyBtn && apiKeyInput) {
      saveKeyBtn.addEventListener("click", () => {
        const prov = providerSelect ? providerSelect.value : "gemini";
        saveApiKey(prov, apiKeyInput.value.trim());
        APIClient.showToast(`Saved API Key for ${prov.toUpperCase()}`, "success");
      });
    }

    if (sendBtn && chatInput) {
      sendBtn.addEventListener("click", () => sendMainChatMessage(chatInput, chatContainer));
      chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          sendMainChatMessage(chatInput, chatContainer);
        }
      });
    }

    if (chipsContainer) {
      renderPromptChips(chipsContainer, (promptText) => {
        if (chatInput) {
          chatInput.value = promptText;
          sendMainChatMessage(chatInput, chatContainer);
        }
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        chatContainer.innerHTML = "";
        messageHistory = [];
        appendSystemBubble(chatContainer, "👋 Conversation cleared. How can DataLens AI help analyze your dataset?");
      });
    }

    // Initial greeting bubble
    appendSystemBubble(chatContainer, "👋 Hello! I am **DataLens AI**. Ask me anything about dataset quality, column statistics, correlation trends, outliers, or machine learning model recommendations!");
  }

  function updateModelDropdownOptions(provider, modelSelectElem) {
    if (!modelSelectElem) return;
    modelSelectElem.innerHTML = "";

    const modelsMap = {
      builtin: [{ val: "builtin-engine", label: "DataLens Fast Heuristic Engine (Offline)" }],
      gemini: [
        { val: "gemini-1.5-flash", label: "Gemini 1.5 Flash (Recommended Free)" },
        { val: "gemini-2.0-flash", label: "Gemini 2.0 Flash" },
        { val: "gemini-1.5-pro", label: "Gemini 1.5 Pro" }
      ],
      groq: [
        { val: "llama-3.3-70b-versatile", label: "Llama 3.3 70B Versatile (Free & Ultra Fast)" },
        { val: "mixtral-8x7b-32768", label: "Mixtral 8x7B" },
        { val: "gemma2-9b-it", label: "Gemma2 9B IT" }
      ],
      openrouter: [
        { val: "google/gemini-2.0-flash-exp:free", label: "Gemini 2.0 Flash Exp (Free)" },
        { val: "meta-llama/llama-3.2-11b-vision-instruct:free", label: "Llama 3.2 11B Free" },
        { val: "deepseek/deepseek-r1:free", label: "DeepSeek R1 Free" }
      ],
      huggingface: [
        { val: "mistralai/Mistral-7B-Instruct-v0.3", label: "Mistral 7B Instruct v0.3" }
      ]
    };

    const list = modelsMap[provider] || modelsMap.builtin;
    list.forEach(m => {
      const opt = document.createElement("option");
      opt.value = m.val;
      opt.textContent = m.label;
      modelSelectElem.appendChild(opt);
    });
    activeModel = list[0].val;
  }

  async function sendMainChatMessage(inputElem, containerElem) {
    const text = inputElem.value.trim();
    if (!text) return;

    const datasetId = APIClient.getActiveDatasetId();
    if (!datasetId) {
      APIClient.showToast("Please upload or select a dataset first.", "error");
      return;
    }

    // Append User message bubble
    appendUserBubble(containerElem, text);
    inputElem.value = "";

    // Append Loading indicator
    const loadingElem = appendLoadingBubble(containerElem);

    const providerSelect = document.getElementById("ai-provider-select");
    const modelSelect = document.getElementById("ai-model-select");
    const prov = providerSelect ? providerSelect.value : "builtin";
    const mod = modelSelect ? modelSelect.value : "";
    const apiKey = getApiKeyForProvider(prov);

    try {
      const res = await APIClient.request("/api/chatbot/query", {
        method: "POST",
        body: JSON.stringify({
          datasetId,
          message: text,
          provider: prov,
          apiKey: apiKey,
          model: mod
        })
      });

      loadingElem.remove();
      appendAssistantBubble(containerElem, res.reply, res.suggestions);
    } catch (err) {
      loadingElem.remove();
      appendAssistantBubble(containerElem, `❌ Error querying AI chatbot: ${err.message || err}`);
    }
  }

  function appendUserBubble(container, text) {
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble user";
    bubble.textContent = text;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  }

  function appendAssistantBubble(container, replyText, suggestions = []) {
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble assistant";
    bubble.innerHTML = formatMarkdownText(replyText);

    if (suggestions && suggestions.length > 0) {
      const sugDiv = document.createElement("div");
      sugDiv.style.marginTop = "12px";
      sugDiv.style.display = "flex";
      sugDiv.style.flexWrap = "wrap";
      sugDiv.style.gap = "6px";

      suggestions.forEach(sug => {
        const chip = document.createElement("button");
        chip.className = "prompt-chip";
        chip.textContent = sug;
        chip.onclick = () => {
          const mainInput = document.getElementById("main-chat-input") || document.getElementById("drawer-chat-input");
          if (mainInput) {
            mainInput.value = sug;
            const mainSend = document.getElementById("main-chat-send") || document.getElementById("drawer-chat-send");
            if (mainSend) mainSend.click();
          }
        };
        sugDiv.appendChild(chip);
      });
      bubble.appendChild(sugDiv);
    }

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  }

  function appendSystemBubble(container, text) {
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble assistant";
    bubble.innerHTML = formatMarkdownText(text);
    container.appendChild(bubble);
  }

  function appendLoadingBubble(container) {
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble assistant";
    bubble.innerHTML = "<em>Analyzing dataset and generating insights... ⏳</em>";
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
    return bubble;
  }

  function renderPromptChips(container, onSelect) {
    container.innerHTML = "";
    PRESET_SUGGESTIONS.forEach(p => {
      const chip = document.createElement("button");
      chip.className = "prompt-chip";
      chip.textContent = p;
      chip.onclick = () => onSelect(p);
      container.appendChild(chip);
    });
  }

  function formatMarkdownText(text) {
    if (!text) return "";
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Bold text **bold**
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Code blocks `code`
    html = html.replace(/`(.*?)`/g, "<code>$1</code>");
    // Line breaks & lists
    html = html.replace(/\n- (.*?)/g, "<br>• $1");
    html = html.replace(/\n\n/g, "<br><br>");
    html = html.replace(/\n/g, "<br>");
    return html;
  }

  // --- Floating Chat Assistant Drawer for All Pages ---
  function initFloatingChatDrawer() {
    if (document.getElementById("floating-chat-trigger-btn")) return;

    const triggerBtn = document.createElement("button");
    triggerBtn.id = "floating-chat-trigger-btn";
    triggerBtn.className = "floating-chat-trigger";
    triggerBtn.innerHTML = "💬 <span>Ask DataLens AI</span>";

    const drawer = document.createElement("div");
    drawer.id = "floating-chat-drawer";
    drawer.className = "chat-drawer";
    drawer.innerHTML = `
      <div class="chat-header">
        <div style="display:flex; align-items:center; gap:8px;">
          <span style="font-size:18px;">🤖</span>
          <strong>DataLens Assistant</strong>
        </div>
        <button id="close-chat-drawer" style="background:none; border:none; color:var(--text-main); font-size:18px; cursor:pointer;">✕</button>
      </div>
      <div id="drawer-chat-messages" class="chat-messages-container"></div>
      <div id="drawer-chat-chips" class="prompt-chips-container" style="max-height:80px; overflow-y:auto;"></div>
      <div class="chat-input-wrapper">
        <textarea id="drawer-chat-input" class="chat-input" rows="1" placeholder="Ask a question about this dataset..."></textarea>
        <button id="drawer-chat-send" class="chat-send-btn">Send</button>
      </div>
    `;

    document.body.appendChild(triggerBtn);
    document.body.appendChild(drawer);

    const drawerMessages = document.getElementById("drawer-chat-messages");
    const drawerChips = document.getElementById("drawer-chat-chips");
    const drawerInput = document.getElementById("drawer-chat-input");
    const drawerSend = document.getElementById("drawer-chat-send");
    const closeBtn = document.getElementById("close-chat-drawer");

    triggerBtn.addEventListener("click", () => {
      drawer.classList.toggle("active");
      if (drawer.classList.contains("active") && drawerMessages.children.length === 0) {
        appendSystemBubble(drawerMessages, "👋 Hi! Ask me anything about your active dataset metrics, trends, or quality!");
        renderPromptChips(drawerChips, (promptText) => {
          drawerInput.value = promptText;
          drawerSend.click();
        });
      }
    });

    closeBtn.addEventListener("click", () => {
      drawer.classList.remove("active");
    });

    drawerSend.addEventListener("click", async () => {
      const text = drawerInput.value.trim();
      if (!text) return;

      const datasetId = APIClient.getActiveDatasetId();
      if (!datasetId) {
        APIClient.showToast("Please upload or select a dataset first.", "error");
        return;
      }

      appendUserBubble(drawerMessages, text);
      drawerInput.value = "";
      const loading = appendLoadingBubble(drawerMessages);

      try {
        const res = await APIClient.request("/api/chatbot/query", {
          method: "POST",
          body: JSON.stringify({ datasetId, message: text, provider: "builtin" })
        });
        loading.remove();
        appendAssistantBubble(drawerMessages, res.reply, res.suggestions);
      } catch (err) {
        loading.remove();
        appendAssistantBubble(drawerMessages, `❌ Error: ${err.message || err}`);
      }
    });

    drawerInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        drawerSend.click();
      }
    });
  }

})();
