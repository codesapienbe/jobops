"use strict";
(() => {
  // src/popup.ts
  document.addEventListener("DOMContentLoaded", async () => {
    let jobData = {};
    const generateBtn = document.getElementById("generate");
    const refreshBtn = document.getElementById("refresh-ollama");
    const status = document.getElementById("clip-status");
    const backendUrl = typeof JOBOPS_BACKEND_URL !== "undefined" ? JOBOPS_BACKEND_URL : "http://localhost:8877";
    chrome.storage.sync.set({ jobops_backend_url: backendUrl }, async () => {
      if (generateBtn) {
        const ollamaAvailable = await isOllamaAvailable();
        generateBtn.style.display = ollamaAvailable ? "" : "none";
      }
      requestJobData();
    });
    if (refreshBtn) {
      refreshBtn.onclick = async () => {
        refreshBtn.disabled = true;
        status.textContent = "Checking Ollama status...";
        const ollamaAvailable = await isOllamaAvailable();
        if (generateBtn)
          generateBtn.style.display = ollamaAvailable ? "" : "none";
        status.textContent = ollamaAvailable ? "Ollama is available." : "Ollama is NOT available.";
        setTimeout(() => {
          status.textContent = "";
        }, 2e3);
        refreshBtn.disabled = false;
      };
    }
    chrome.runtime.onMessage.addListener((msg, _sender, _sendResponse) => {
      if (msg.action === "show_preview" && msg.jobData) {
        jobData = msg.jobData;
        renderPreview(jobData);
      }
    });
    function requestJobData() {
      console.info("[JobOps Clipper] Requesting job data from content script...");
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (!tabs[0]?.id)
          return;
        chrome.scripting.executeScript(
          {
            target: { tabId: tabs[0].id },
            func: () => !!window && !!window.document && !!window.document.body
          },
          (results) => {
            if (chrome.runtime.lastError || !results || !results[0].result) {
              document.getElementById("clip-status").textContent = "Content script not loaded. Please refresh the page and try again.";
              return;
            }
            chrome.tabs.sendMessage(
              tabs[0].id,
              { action: "clip_page" },
              (response) => {
                if (chrome.runtime.lastError) {
                  document.getElementById("clip-status").textContent = "Could not connect to content script. Try refreshing the page.";
                  return;
                }
                if (response && response.jobData) {
                  jobData = response.jobData;
                  renderPreview(jobData);
                }
              }
            );
          }
        );
      });
    }
    document.getElementById("approve").onclick = async () => {
      if (!jobData || Object.keys(jobData).length === 0)
        return;
      const jsonString = JSON.stringify(jobData, null, 2);
      try {
        await navigator.clipboard.writeText(jsonString);
        document.getElementById("clip-status").textContent = "Copied to clipboard!";
        setTimeout(() => window.close(), 1200);
      } catch (e) {
        document.getElementById("clip-status").textContent = "Failed to copy to clipboard.";
      }
    };
    document.getElementById("generate").onclick = async () => {
      const generateBtn2 = document.getElementById("generate");
      const status2 = document.getElementById("clip-status");
      const progressBar = document.getElementById("progress-bar");
      if (!jobData || Object.keys(jobData).length === 0)
        return;
      generateBtn2.disabled = true;
      status2.textContent = "Checking Ollama model...";
      progressBar.style.display = "block";
      try {
        const modelAvailable = await isOllamaModelAvailable(OLLAMA_MODEL);
        if (!modelAvailable) {
          status2.textContent = `Ollama model '${OLLAMA_MODEL}' is not available. Please pull it with 'ollama pull ${OLLAMA_MODEL}' and try again.`;
          progressBar.style.display = "none";
          generateBtn2.disabled = false;
          return;
        }
        status2.textContent = "Generating structured data...";
        const enhanced = await enhanceWithOllama(jobData);
        jobData = enhanced;
        renderPreview(jobData);
        status2.textContent = "Structured data generated.";
      } catch (e) {
        status2.textContent = "Failed to generate structured data: " + (e?.message || e);
      } finally {
        progressBar.style.display = "none";
        generateBtn2.disabled = false;
      }
    };
    document.getElementById("cancel").onclick = () => window.close();
  });
  function renderMarkdown(md) {
    return md.replace(/^### (.*$)/gim, "<h3>$1</h3>").replace(/^## (.*$)/gim, "<h2>$1</h2>").replace(/^# (.*$)/gim, "<h1>$1</h1>").replace(/\*\*(.*?)\*\*/gim, "<b>$1</b>").replace(/\*(.*?)\*/gim, "<i>$1</i>").replace(/!\[(.*?)\]\((.*?)\)/gim, '<img alt="$1" src="$2" style="max-width:100px;max-height:100px;border-radius:8px;margin:2px 8px 2px 0;vertical-align:middle;" />').replace(/\[(.*?)\]\((.*?)\)/gim, '<a href="$2" target="_blank">$1</a>').replace(/`([^`]+)`/gim, "<code>$1</code>").replace(/\n/g, "<br>");
  }
  function renderPreview(jobData) {
    const container = document.getElementById("preview-container") || document.createElement("div");
    container.id = "preview-container";
    let md = "";
    if (jobData.title)
      md += `# ${jobData.title}
`;
    if (jobData.body)
      md += `
${jobData.body}
`;
    if (jobData.metaKeywords && Array.isArray(jobData.metaKeywords) && jobData.metaKeywords.length > 0) {
      md += `
## Tags
`;
      md += jobData.metaKeywords.map((kw) => ` [32m [1m${kw} [0m`).join(" ");
      md += "\n";
    }
    if (jobData.headings && Array.isArray(jobData.headings) && jobData.headings.length > 0) {
      md += `
## Headings
`;
      for (const h of jobData.headings) {
        md += `- <b>${escapeHtml(h.text)}</b> <span style='opacity:0.7;'>(${escapeHtml(h.tag)})</span>
`;
      }
      md += "\n";
    }
    if (jobData.images && Array.isArray(jobData.images) && jobData.images.length > 0) {
      md += `
## Images
`;
      for (const img of jobData.images) {
        md += `![${img.alt || ""}](${img.src}) `;
      }
      md += "\n";
    }
    const skipKeys = /* @__PURE__ */ new Set(["title", "body", "metaKeywords", "headings", "images"]);
    for (const [key, value] of Object.entries(jobData)) {
      if (skipKeys.has(key))
        continue;
      if (typeof value === "string" && value.trim() !== "") {
        md += `
## ${key.charAt(0).toUpperCase() + key.slice(1)}
${escapeHtml(value)}
`;
      } else if (Array.isArray(value) && value.length > 0) {
        md += `
## ${key.charAt(0).toUpperCase() + key.slice(1)}
`;
        md += value.map((v) => `- ${escapeHtml(typeof v === "string" ? v : JSON.stringify(v))}`).join("\n");
        md += "\n";
      }
    }
    if (jobData.url)
      md += `
[Source](${jobData.url})
`;
    container.innerHTML = `<div class="jobops-markdown-preview">${renderMarkdown(md)}</div>`;
    const parent = document.querySelector(".glassmorphic-popup") || document.body;
    let old = document.getElementById("preview-container");
    if (old)
      old.replaceWith(container);
    else
      parent.insertBefore(container, parent.firstChild);
  }
  function escapeHtml(str) {
    return str.replace(/[&<>"']/g, function(c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c] || c;
    });
  }
  var OLLAMA_URL = "http://localhost:11434";
  var OLLAMA_MODEL = "qwen3:1.7b";
  var jobSchema = {
    type: "object",
    properties: {
      title: { type: "string" },
      url: { type: "string" },
      body: { type: "string" },
      metaDescription: { type: "string" },
      metaKeywords: { type: "array", items: { type: "string" } },
      ogType: { type: "string" },
      ogSiteName: { type: "string" },
      canonical: { type: "string" },
      headings: {
        type: "array",
        items: {
          type: "object",
          properties: {
            tag: { type: "string" },
            text: { type: "string" }
          },
          required: ["tag", "text"]
        }
      },
      images: {
        type: "array",
        items: {
          type: "object",
          properties: {
            src: { type: "string" },
            alt: { type: "string" }
          },
          required: ["src"]
        }
      },
      selectedText: { type: "string" },
      created_at: { type: "string" },
      jobops_action: { type: "string" }
    },
    required: ["title", "url", "body", "created_at", "jobops_action"]
  };
  async function enhanceWithOllama(jobData) {
    const prompt = `Extract and complete the following job data as JSON.`;
    console.info("[JobOps Clipper] Sending prompt to Ollama:", prompt, jobData);
    const response = await fetch(`${OLLAMA_URL}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: OLLAMA_MODEL,
        prompt,
        format: jobSchema,
        stream: false,
        data: jobData
        // Optionally send jobData as context
      })
    });
    if (!response.ok) {
      let errorMsg = "Ollama API error";
      try {
        const err = await response.json();
        errorMsg += `
Status: ${response.status} ${response.statusText}`;
        errorMsg += `
Headers: ${JSON.stringify(Object.fromEntries(response.headers.entries()))}`;
        errorMsg += `
Body: ${JSON.stringify(err)}`;
        console.error("[JobOps Clipper] Ollama API error:", errorMsg);
      } catch (e) {
        try {
          const text = await response.text();
          errorMsg += `
Status: ${response.status} ${response.statusText}`;
          errorMsg += `
Headers: ${JSON.stringify(Object.fromEntries(response.headers.entries()))}`;
          errorMsg += `
Body: ${text}`;
          console.error("[JobOps Clipper] Ollama API error:", errorMsg);
        } catch {
        }
      }
      throw new Error(errorMsg);
    }
    const data = await response.json();
    let completed;
    try {
      completed = JSON.parse(data.response);
    } catch {
      completed = jobData;
    }
    return { ...jobData, ...completed };
  }
  async function isOllamaModelAvailable(model) {
    try {
      const response = await fetch(`${OLLAMA_URL}/api/tags`);
      if (!response.ok)
        return false;
      const data = await response.json();
      if (!data.models || !Array.isArray(data.models))
        return false;
      return data.models.some((m) => m.name === model);
    } catch {
      return false;
    }
  }
  async function isOllamaAvailable() {
    try {
      const response = await fetch(`${OLLAMA_URL}/api/tags`);
      return response.ok;
    } catch {
      return false;
    }
  }
})();
