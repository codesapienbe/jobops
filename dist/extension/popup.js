"use strict";
(() => {
  // src/popup.ts
  document.addEventListener("DOMContentLoaded", async () => {
    let jobData = {};
    const markdownEditor = document.getElementById("markdown-editor");
    const copyBtn = document.getElementById("copy-markdown");
    const status = document.getElementById("clip-status");
    const propTitle = document.getElementById("prop-title");
    const propUrl = document.getElementById("prop-url");
    const propAuthor = document.getElementById("prop-author");
    const propPublished = document.getElementById("prop-published");
    const propCreated = document.getElementById("prop-created");
    const propDescription = document.getElementById("prop-description");
    const propTags = document.getElementById("prop-tags");
    const propHeadings = document.getElementById("prop-headings");
    const propImages = document.getElementById("prop-images");
    const propLocation = document.getElementById("prop-location");
    const autoMapBtn = document.getElementById("auto-map-ollama");
    copyBtn.disabled = false;
    setupToggleHandlers();
    const backendUrl = typeof JOBOPS_BACKEND_URL !== "undefined" ? JOBOPS_BACKEND_URL : "http://localhost:8877";
    chrome.storage.sync.set({ jobops_backend_url: backendUrl }, async () => {
      requestJobData();
    });
    chrome.runtime.onMessage.addListener((msg, _sender, _sendResponse) => {
      if (msg.action === "show_preview" && msg.jobData) {
        jobData = msg.jobData;
        populatePropertyFields(jobData);
        markdownEditor.value = generateMarkdown(jobData);
        copyBtn.disabled = false;
      }
    });
    function setupToggleHandlers() {
      const toggleHeaders = document.querySelectorAll(".properties-header, .markdown-header");
      toggleHeaders.forEach((header) => {
        header.addEventListener("click", () => {
          const toggleTarget = header.getAttribute("data-toggle");
          if (toggleTarget) {
            toggleSection(toggleTarget);
          }
        });
      });
    }
    function toggleSection(sectionId) {
      const content = document.getElementById(sectionId);
      const header = content?.parentElement?.querySelector(".properties-header, .markdown-header");
      const toggleIcon = header?.querySelector(".toggle-icon");
      if (content && header && toggleIcon) {
        const isCollapsed = content.classList.contains("collapsed");
        if (isCollapsed) {
          content.classList.remove("collapsed");
          content.classList.add("expanded");
          toggleIcon.textContent = "\u25BC";
        } else {
          content.classList.remove("expanded");
          content.classList.add("collapsed");
          toggleIcon.textContent = "\u25B6";
        }
      }
    }
    function populatePropertyFields(data) {
      propTitle.value = data.title || "";
      propUrl.value = data.url || "";
      propAuthor.value = data.author || "";
      propPublished.value = data.published || "";
      propCreated.value = data.created_at || "";
      propDescription.value = data.description || "";
      propTags.value = Array.isArray(data.metaKeywords) ? data.metaKeywords.join(", ") : data.metaKeywords || "";
      propLocation.value = data.location || "";
      propHeadings.innerHTML = "";
      if (Array.isArray(data.headings) && data.headings.length > 0) {
        for (const h of data.headings) {
          const tag = document.createElement("span");
          tag.className = "property-tag";
          tag.textContent = h.text + (h.tag ? ` (${h.tag})` : "");
          propHeadings.appendChild(tag);
        }
      }
      propImages.innerHTML = "";
      if (Array.isArray(data.images) && data.images.length > 0) {
        for (const img of data.images) {
          const thumb = document.createElement("img");
          thumb.className = "property-image-thumb";
          thumb.src = img.src;
          thumb.alt = img.alt || "";
          thumb.title = img.alt || img.src;
          propImages.appendChild(thumb);
        }
      }
    }
    function updateJobDataFromFields() {
      jobData.title = propTitle.value;
      jobData.url = propUrl.value;
      jobData.author = propAuthor.value;
      jobData.published = propPublished.value;
      jobData.created_at = propCreated.value;
      jobData.description = propDescription.value;
      jobData.metaKeywords = propTags.value.split(",").map((t) => t.trim()).filter(Boolean);
      jobData.location = propLocation.value;
      markdownEditor.value = generateMarkdown(jobData);
    }
    [propTitle, propUrl, propAuthor, propPublished, propCreated, propDescription, propTags, propLocation].forEach((input) => {
      input.addEventListener("input", updateJobDataFromFields);
    });
    function requestJobData() {
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
              status.textContent = "Content script not loaded. Please refresh the page and try again.";
              return;
            }
            chrome.tabs.sendMessage(
              tabs[0].id,
              { action: "clip_page" },
              (response) => {
                if (chrome.runtime.lastError) {
                  status.textContent = "Could not connect to content script. Try refreshing the page.";
                  return;
                }
                if (response && response.jobData) {
                  jobData = response.jobData;
                  populatePropertyFields(jobData);
                  markdownEditor.value = generateMarkdown(jobData);
                  copyBtn.disabled = false;
                }
              }
            );
          }
        );
      });
    }
    copyBtn.onclick = async () => {
      try {
        const contentToCopy = markdownEditor.value || generateMarkdown(jobData);
        if (!contentToCopy.trim()) {
          showNotification("No content to copy!", true);
          return;
        }
        await navigator.clipboard.writeText(contentToCopy);
        showNotification("\u2705 Content copied to clipboard!");
        status.textContent = "Copied to clipboard!";
        setTimeout(() => status.textContent = "", 2e3);
      } catch (e) {
        console.error("Copy failed:", e);
        showNotification("\u274C Failed to copy to clipboard", true);
        status.textContent = "Failed to copy to clipboard.";
      }
    };
    function showNotification(message, isError = false) {
      if (chrome.notifications) {
        chrome.notifications.create({
          type: "basic",
          iconUrl: "icon.png",
          title: "JobOps Clipper",
          message,
          priority: isError ? 2 : 1
        });
      } else {
        status.textContent = message;
        setTimeout(() => status.textContent = "", 3e3);
      }
    }
    autoMapBtn.onclick = async () => {
      autoMapBtn.disabled = true;
      status.textContent = "Auto-mapping with Ollama...";
      try {
        const enhanced = await enhanceWithOllama(jobData);
        jobData = enhanced;
        populatePropertyFields(jobData);
        markdownEditor.value = generateMarkdown(jobData);
        status.textContent = "Fields auto-mapped!";
        copyBtn.disabled = false;
      } catch (e) {
        status.textContent = "Ollama mapping failed: " + (e?.message || e);
        copyBtn.disabled = false;
      } finally {
        autoMapBtn.disabled = false;
        setTimeout(() => status.textContent = "", 2e3);
      }
    };
  });
  function generateMarkdown(jobData) {
    let md = "";
    if (jobData.title)
      md += `# ${jobData.title}
`;
    if (jobData.body)
      md += `
${jobData.body}
`;
    if (jobData.location)
      md += `
**Location:** ${jobData.location}
`;
    if (jobData.metaKeywords && Array.isArray(jobData.metaKeywords) && jobData.metaKeywords.length > 0) {
      md += `
## Tags
`;
      md += jobData.metaKeywords.map((kw) => `**${kw}**`).join(" ");
      md += "\n";
    }
    const skipKeys = /* @__PURE__ */ new Set(["title", "body", "metaKeywords", "headings", "images"]);
    for (const [key, value] of Object.entries(jobData)) {
      if (skipKeys.has(key))
        continue;
      if (typeof value === "string" && value.trim() !== "") {
        md += `
## ${key.charAt(0).toUpperCase() + key.slice(1)}
${value}
`;
      } else if (Array.isArray(value) && value.length > 0) {
        md += `
## ${key.charAt(0).toUpperCase() + key.slice(1)}
`;
        md += value.map((v) => `- ${typeof v === "string" ? v : JSON.stringify(v)}`).join("\n");
        md += "\n";
      }
    }
    if (jobData.url)
      md += `
[Source](${jobData.url})
`;
    return md;
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
})();
