"use strict";
(() => {
  // src/popup.ts
  var GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions";
  var GROQ_MODEL = "qwen2.5-32b-instant";
  var OLLAMA_URL = "http://localhost:11434";
  var OLLAMA_MODEL = "qwen3:1.7b";
  document.addEventListener("DOMContentLoaded", async () => {
    let jobData = {};
    let resumeContent = "";
    const markdownEditor = document.getElementById("markdown-editor");
    const copyBtn = document.getElementById("copy-markdown");
    const generateReportBtn = document.getElementById("generate-report");
    const settingsBtn = document.getElementById("settings");
    const status = document.getElementById("clip-status");
    const resumeUpload = document.getElementById("resume-upload");
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
    copyBtn.disabled = false;
    generateReportBtn.disabled = false;
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
        generateReportBtn.disabled = false;
      }
    });
    resumeUpload.addEventListener("change", handleResumeUpload);
    generateReportBtn.addEventListener("click", handleGenerateReport);
    settingsBtn.addEventListener("click", handleSettings);
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
    async function handleResumeUpload(event) {
      const target = event.target;
      const file = target.files?.[0];
      if (!file) {
        showNotification("No file selected", true);
        return;
      }
      if (file.type !== "application/pdf") {
        showNotification("Please select a PDF file", true);
        return;
      }
      try {
        status.textContent = "Extracting resume content...";
        resumeContent = await extractPdfContent(file);
        showNotification("\u2705 Resume content extracted successfully!");
        status.textContent = "Resume ready for report generation";
      } catch (error) {
        console.error("PDF extraction failed:", error);
        showNotification("\u274C Failed to extract PDF content", true);
        status.textContent = "PDF extraction failed";
      }
    }
    async function handleGenerateReport() {
      if (!resumeContent) {
        resumeUpload.click();
        return;
      }
      generateReportBtn.disabled = true;
      status.textContent = "Generating comprehensive report...";
      try {
        const report = await generateJobReport(jobData, resumeContent);
        markdownEditor.value = report;
        showNotification("\u2705 Report generated successfully!");
        status.textContent = "Report generated and ready to copy";
      } catch (error) {
        console.error("Report generation failed:", error);
        const errorMessage = error instanceof Error ? error.message : String(error);
        if (errorMessage.includes("API key")) {
          showNotification("\u274C Groq API key not configured. Please set it in extension settings.", true);
          status.textContent = "API key required - check extension settings";
        } else {
          showNotification("\u274C Report generation failed", true);
          status.textContent = "Report generation failed";
        }
      } finally {
        generateReportBtn.disabled = false;
        setTimeout(() => status.textContent = "", 3e3);
      }
    }
    async function handleSettings() {
      const apiKey = await getGroqApiKey();
      const newApiKey = prompt("Enter your Groq API key (leave empty to remove):", apiKey || "");
      if (newApiKey !== null) {
        if (newApiKey.trim()) {
          await new Promise((resolve) => {
            chrome.storage.sync.set({ groq_api_key: newApiKey.trim() }, () => {
              showNotification("\u2705 Groq API key saved!");
              resolve();
            });
          });
        } else {
          await new Promise((resolve) => {
            chrome.storage.sync.remove(["groq_api_key"], () => {
              showNotification("\u2705 Groq API key removed!");
              resolve();
            });
          });
        }
      }
    }
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
  async function extractPdfContent(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = async function(e) {
        try {
          const typedarray = new Uint8Array(e.target?.result);
          const pdfjsLib = window["pdfjs-dist/build/pdf"];
          if (!pdfjsLib) {
            const script = document.createElement("script");
            script.src = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
            script.onload = () => extractPdfWithLibrary(typedarray, resolve, reject);
            script.onerror = () => reject(new Error("Failed to load PDF.js"));
            document.head.appendChild(script);
          } else {
            extractPdfWithLibrary(typedarray, resolve, reject);
          }
        } catch (error) {
          reject(error);
        }
      };
      reader.onerror = () => reject(new Error("Failed to read file"));
      reader.readAsArrayBuffer(file);
    });
  }
  async function extractPdfWithLibrary(typedarray, resolve, reject) {
    try {
      const pdfjsLib = window["pdfjs-dist/build/pdf"];
      const loadingTask = pdfjsLib.getDocument({ data: typedarray });
      const pdf = await loadingTask.promise;
      let fullText = "";
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        const pageText = textContent.items.map((item) => item.str).join(" ");
        fullText += pageText + "\n";
      }
      resolve(fullText.trim());
    } catch (error) {
      reject(new Error(`PDF extraction failed: ${error}`));
    }
  }
  async function generateJobReport(jobData, resumeContent) {
    const prompt2 = `You are an expert job application analyst. Based on the provided job posting data and resume content, generate a comprehensive job application tracking report.

Job Posting Data:
${JSON.stringify(jobData, null, 2)}

Resume Content:
${resumeContent}

Please analyze this information and fill out the job application tracking report template. Extract all relevant information from both the job posting and resume to populate the template fields. Use your analysis to:

1. Identify skills matches and gaps
2. Suggest interview preparation strategies
3. Provide actionable insights for the application process
4. Create realistic timelines and goals
5. Offer specific recommendations for improvement

Fill in all template placeholders with concrete, actionable information based on the provided data.`;
    try {
      const groqResponse = await callGroqAPI(prompt2);
      if (groqResponse) {
        return groqResponse;
      }
    } catch (error) {
      console.warn("Groq API failed, falling back to Ollama:", error);
    }
    try {
      const ollamaResponse = await callOllamaAPI(prompt2);
      if (ollamaResponse) {
        return ollamaResponse;
      }
    } catch (error) {
      console.error("Ollama API also failed:", error);
    }
    throw new Error("Both Groq and Ollama APIs failed");
  }
  async function callGroqAPI(prompt2) {
    try {
      const apiKey = await getGroqApiKey();
      if (!apiKey) {
        console.warn("No Groq API key found");
        throw new Error("Groq API key not configured");
      }
      const response = await fetch(GROQ_API_URL, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${apiKey}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          model: GROQ_MODEL,
          messages: [
            {
              role: "system",
              content: "You are an expert job application analyst and career advisor. Provide comprehensive, actionable insights and fill out templates completely."
            },
            {
              role: "user",
              content: prompt2
            }
          ],
          temperature: 0.3,
          max_tokens: 4e3,
          stream: false
        })
      });
      if (!response.ok) {
        throw new Error(`Groq API error: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      return data.choices?.[0]?.message?.content || null;
    } catch (error) {
      console.error("Groq API call failed:", error);
      return null;
    }
  }
  async function callOllamaAPI(prompt2) {
    try {
      const response = await fetch(`${OLLAMA_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: OLLAMA_MODEL,
          prompt: prompt2,
          stream: false
        })
      });
      if (!response.ok) {
        throw new Error(`Ollama API error: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      return data.response || null;
    } catch (error) {
      console.error("Ollama API call failed:", error);
      return null;
    }
  }
  async function getGroqApiKey() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(["groq_api_key"], (result) => {
        resolve(result.groq_api_key || null);
      });
    });
  }
})();
