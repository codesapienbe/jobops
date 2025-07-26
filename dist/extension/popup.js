"use strict";
(() => {
  // src/popup.ts
  var GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions";
  var GROQ_MODEL = "qwen2.5-32b-instant";
  var OLLAMA_URL = "http://localhost:11434";
  var OLLAMA_MODEL = "qwen3:1.7b";
  var consoleOutput = null;
  function logToConsole(message, level = "info") {
    if (!consoleOutput)
      return;
    const timestamp = (/* @__PURE__ */ new Date()).toLocaleTimeString();
    const line = document.createElement("div");
    line.className = `console-line ${level}`;
    line.innerHTML = `<span style="color: #888;">[${timestamp}]</span> ${message}`;
    consoleOutput.appendChild(line);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
    console.log(`[${level.toUpperCase()}] ${message}`);
  }
  function clearConsole() {
    if (consoleOutput) {
      consoleOutput.innerHTML = "";
      logToConsole("\u{1F9F9} Console cleared", "info");
    }
  }
  document.addEventListener("DOMContentLoaded", async () => {
    let jobData = {};
    let resumeContent = "";
    const markdownEditor = document.getElementById("markdown-editor");
    const copyBtn = document.getElementById("copy-markdown");
    const generateReportBtn = document.getElementById("generate-report");
    const settingsBtn = document.getElementById("settings");
    const status = document.getElementById("clip-status");
    if (!status) {
      console.error("Status element not found!");
    }
    const resumeUpload = document.getElementById("resume-upload");
    consoleOutput = document.getElementById("console-output");
    const clearConsoleBtn = document.getElementById("clear-console");
    if (!consoleOutput) {
      console.error("Console output element not found!");
    } else {
      logToConsole("\u{1F50D} Console monitor initialized", "info");
    }
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
        logToConsole("\u{1F4E8} Received preview data from content script", "info");
        logToConsole(`\u{1F4CA} Job title: ${msg.jobData.title || "N/A"}`, "info");
        jobData = msg.jobData;
        populatePropertyFields(jobData);
        markdownEditor.value = generateMarkdown(jobData);
        copyBtn.disabled = false;
        generateReportBtn.disabled = false;
        logToConsole("\u2705 Preview data processed successfully", "success");
      }
    });
    if (resumeUpload) {
      console.log("Resume upload element found, adding event listener");
      resumeUpload.addEventListener("change", handleResumeUpload);
    } else {
      console.error("Resume upload element not found!");
    }
    generateReportBtn.addEventListener("click", handleGenerateReport);
    settingsBtn.addEventListener("click", handleSettings);
    if (clearConsoleBtn) {
      clearConsoleBtn.addEventListener("click", clearConsole);
    }
    logToConsole("\u{1F680} JobOps Clipper initialized", "info");
    logToConsole("\u{1F4CB} Ready to process job postings and resumes", "success");
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
      logToConsole("\u{1F310} Requesting job data from current page...", "info");
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (!tabs[0]?.id) {
          logToConsole("\u274C No active tab found", "error");
          return;
        }
        logToConsole("\u{1F50D} Checking content script availability...", "debug");
        chrome.scripting.executeScript(
          {
            target: { tabId: tabs[0].id },
            func: () => !!window && !!window.document && !!window.document.body
          },
          (results) => {
            if (chrome.runtime.lastError || !results || !results[0].result) {
              logToConsole("\u274C Content script not loaded. Please refresh the page and try again.", "error");
              status.textContent = "Content script not loaded. Please refresh the page and try again.";
              return;
            }
            logToConsole("\u2705 Content script available, requesting page data...", "success");
            chrome.tabs.sendMessage(
              tabs[0].id,
              { action: "clip_page" },
              (response) => {
                if (chrome.runtime.lastError) {
                  logToConsole("\u274C Could not connect to content script. Try refreshing the page.", "error");
                  status.textContent = "Could not connect to content script. Try refreshing the page.";
                  return;
                }
                if (response && response.jobData) {
                  logToConsole("\u2705 Job data received successfully!", "success");
                  logToConsole(`\u{1F4CA} Job title: ${response.jobData.title || "N/A"}`, "info");
                  jobData = response.jobData;
                  populatePropertyFields(jobData);
                  markdownEditor.value = generateMarkdown(jobData);
                  copyBtn.disabled = false;
                } else {
                  logToConsole("\u26A0\uFE0F No job data received from content script", "warning");
                }
              }
            );
          }
        );
      });
    }
    copyBtn.onclick = async () => {
      logToConsole("\u{1F4CB} Copy to clipboard triggered", "info");
      try {
        const contentToCopy = markdownEditor.value || generateMarkdown(jobData);
        if (!contentToCopy.trim()) {
          logToConsole("\u274C No content to copy", "error");
          showNotification("No content to copy!", true);
          return;
        }
        logToConsole(`\u{1F4CB} Copying content (${contentToCopy.length} characters) to clipboard...`, "progress");
        await navigator.clipboard.writeText(contentToCopy);
        logToConsole("\u2705 Content copied to clipboard successfully!", "success");
        showNotification("\u2705 Content copied to clipboard!");
        status.textContent = "Copied to clipboard!";
        setTimeout(() => status.textContent = "", 2e3);
      } catch (e) {
        logToConsole(`\u274C Copy failed: ${e}`, "error");
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
      logToConsole("\u{1F4C1} Resume upload triggered", "info");
      const target = event.target;
      const file = target.files?.[0];
      if (!file) {
        logToConsole("\u274C No file selected", "error");
        showNotification("No file selected", true);
        return;
      }
      if (file.type !== "application/pdf") {
        logToConsole("\u274C Invalid file type - PDF required", "error");
        showNotification("Please select a PDF file", true);
        return;
      }
      logToConsole(`\u{1F4C4} Starting PDF extraction: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, "progress");
      try {
        status.textContent = "\u{1F4C4} Loading PDF file...";
        status.className = "loading";
        showNotification("\u{1F4C4} Loading PDF file...");
        logToConsole("\u{1F4C4} Loading PDF file into memory...", "progress");
        status.textContent = "\u{1F50D} Extracting text content from PDF...";
        status.className = "loading";
        showNotification("\u{1F50D} Extracting PDF content...");
        logToConsole("\u{1F50D} Extracting text content from PDF...", "progress");
        resumeContent = await extractPdfContent(file);
        logToConsole(`\u2705 PDF extraction completed! Content length: ${resumeContent.length} characters`, "success");
        status.textContent = "\u2705 Resume content extracted successfully!";
        status.className = "success";
        showNotification("\u2705 Resume content extracted successfully!");
        setTimeout(() => {
          status.textContent = "\u{1F4CB} Resume ready - click \u{1F4CA} Generate Report to continue";
          status.className = "success";
          logToConsole("\u{1F4CB} Resume ready for report generation", "success");
        }, 2e3);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logToConsole(`\u274C PDF extraction failed: ${errorMessage}`, "error");
        status.textContent = `\u274C PDF extraction failed: ${errorMessage}`;
        status.className = "error";
        showNotification(`\u274C Failed to extract PDF content: ${errorMessage}`, true);
      }
    }
    async function handleGenerateReport() {
      if (!resumeContent) {
        logToConsole("\u{1F4C1} No resume content found, triggering file upload", "warning");
        resumeUpload.click();
        return;
      }
      logToConsole("\u{1F680} Starting report generation process", "info");
      generateReportBtn.disabled = true;
      status.textContent = "\u{1F504} Starting report generation...";
      status.className = "loading";
      showNotification("\u{1F504} Starting report generation...");
      try {
        logToConsole("\u{1F511} Checking API configuration...", "progress");
        status.textContent = "\u{1F511} Checking API configuration...";
        status.className = "loading";
        const apiKey = await getGroqApiKey();
        if (!apiKey) {
          throw new Error("Groq API key not configured");
        }
        logToConsole("\u2705 API key found, proceeding with report generation", "success");
        showNotification("\u2705 API key found, proceeding...");
        logToConsole("\u{1F4CA} Preparing job data and resume content...", "progress");
        status.textContent = "\u{1F4CA} Preparing job data and resume content...";
        status.className = "loading";
        showNotification("\u{1F4CA} Preparing data for analysis...");
        logToConsole("\u{1F916} Sending data to Groq API for analysis...", "progress");
        status.textContent = "\u{1F916} Sending data to Groq API for analysis...";
        status.className = "loading";
        showNotification("\u{1F916} Analyzing with Groq API...");
        const report = await generateJobReport(jobData, resumeContent);
        logToConsole("\u2705 Report generated successfully!", "success");
        status.textContent = "\u2705 Report generated successfully!";
        status.className = "success";
        showNotification("\u2705 Report generated successfully!");
        markdownEditor.value = report;
        setTimeout(() => {
          status.textContent = "\u{1F4CB} Report ready - use Copy button to copy content";
          status.className = "success";
          logToConsole("\u{1F4CB} Report ready for copying", "success");
        }, 2e3);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logToConsole(`\u274C Report generation failed: ${errorMessage}`, "error");
        if (errorMessage.includes("API key")) {
          logToConsole("\u{1F527} API key required - please configure in settings", "warning");
          status.textContent = "\u274C API key required - click \u2699\uFE0F to configure";
          status.className = "error";
          showNotification("\u274C Groq API key not configured. Click \u2699\uFE0F to set it up.", true);
        } else if (errorMessage.includes("Groq API")) {
          logToConsole("\u26A0\uFE0F Groq API failed, trying Ollama fallback...", "warning");
          status.textContent = "\u26A0\uFE0F Groq API failed, trying Ollama fallback...";
          status.className = "loading";
          showNotification("\u26A0\uFE0F Groq API failed, trying Ollama...");
          try {
            logToConsole("\u{1F504} Attempting Ollama fallback...", "progress");
            status.textContent = "\u{1F504} Attempting Ollama fallback...";
            status.className = "loading";
            const report = await generateJobReportWithOllama(jobData, resumeContent);
            markdownEditor.value = report;
            logToConsole("\u2705 Report generated with Ollama fallback!", "success");
            status.textContent = "\u2705 Report generated with Ollama!";
            status.className = "success";
            showNotification("\u2705 Report generated with Ollama fallback!");
          } catch (ollamaError) {
            logToConsole("\u274C Both Groq and Ollama failed", "error");
            status.textContent = "\u274C Both Groq and Ollama failed";
            status.className = "error";
            showNotification("\u274C Report generation failed on all services", true);
          }
        } else {
          logToConsole("\u274C Report generation failed with unknown error", "error");
          status.textContent = "\u274C Report generation failed";
          status.className = "error";
          showNotification("\u274C Report generation failed", true);
        }
      } finally {
        generateReportBtn.disabled = false;
      }
    }
    async function handleSettings() {
      logToConsole("\u2699\uFE0F Settings dialog opened", "info");
      const apiKey = await getGroqApiKey();
      const newApiKey = prompt("Enter your Groq API key (leave empty to remove):", apiKey || "");
      if (newApiKey !== null) {
        if (newApiKey.trim()) {
          logToConsole("\u{1F511} Saving new Groq API key...", "progress");
          await new Promise((resolve) => {
            chrome.storage.sync.set({ groq_api_key: newApiKey.trim() }, () => {
              logToConsole("\u2705 Groq API key saved successfully!", "success");
              showNotification("\u2705 Groq API key saved!");
              resolve();
            });
          });
        } else {
          logToConsole("\u{1F5D1}\uFE0F Removing Groq API key...", "warning");
          await new Promise((resolve) => {
            chrome.storage.sync.remove(["groq_api_key"], () => {
              logToConsole("\u2705 Groq API key removed successfully!", "success");
              showNotification("\u2705 Groq API key removed!");
              resolve();
            });
          });
        }
      } else {
        logToConsole("\u274C Settings dialog cancelled", "info");
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
      logToConsole("\u{1F504} Starting PDF content extraction...", "progress");
      const reader = new FileReader();
      reader.onload = async function(e) {
        try {
          logToConsole("\u{1F4D6} File read successfully, creating typed array...", "debug");
          const typedarray = new Uint8Array(e.target?.result);
          logToConsole(`\u{1F4CA} Typed array created, size: ${typedarray.length} bytes`, "debug");
          const pdfjsLib = window["pdfjs-dist/build/pdf"];
          logToConsole(`\u{1F4DA} PDF.js library available: ${!!pdfjsLib}`, "debug");
          if (!pdfjsLib) {
            logToConsole("\u{1F4DA} PDF.js not available, loading dynamically...", "progress");
            const status = document.getElementById("clip-status");
            if (status) {
              status.textContent = "\u{1F4DA} Loading PDF processing library...";
              status.className = "loading";
            }
            const script = document.createElement("script");
            script.src = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
            script.onload = () => {
              logToConsole("\u2705 PDF.js loaded dynamically, proceeding with extraction...", "success");
              extractPdfWithLibrary(typedarray, resolve, reject);
            };
            script.onerror = () => {
              logToConsole("\u274C Failed to load PDF.js from CDN", "error");
              reject(new Error("Failed to load PDF.js"));
            };
            document.head.appendChild(script);
          } else {
            logToConsole("\u2705 PDF.js already available, proceeding with extraction...", "success");
            extractPdfWithLibrary(typedarray, resolve, reject);
          }
        } catch (error) {
          logToConsole(`\u274C Error in PDF extraction: ${error}`, "error");
          reject(error);
        }
      };
      reader.onerror = (error) => {
        logToConsole(`\u274C FileReader error: ${error}`, "error");
        reject(new Error("Failed to read file"));
      };
      reader.readAsArrayBuffer(file);
    });
  }
  async function extractPdfWithLibrary(typedarray, resolve, reject) {
    try {
      logToConsole("\u{1F504} Starting PDF library extraction...", "progress");
      const pdfjsLib = window["pdfjs-dist/build/pdf"];
      if (!pdfjsLib) {
        throw new Error("PDF.js library not available");
      }
      const status = document.getElementById("clip-status");
      if (status) {
        status.textContent = "\u{1F4D6} Loading PDF document...";
        status.className = "loading";
      }
      logToConsole("\u{1F4D6} Creating PDF document from typed array...", "progress");
      const loadingTask = pdfjsLib.getDocument({ data: typedarray });
      const pdf = await loadingTask.promise;
      logToConsole(`\u{1F4C4} PDF document loaded, pages: ${pdf.numPages}`, "success");
      let fullText = "";
      const totalPages = pdf.numPages;
      for (let i = 1; i <= totalPages; i++) {
        logToConsole(`\u{1F4C4} Processing page ${i} of ${totalPages}...`, "progress");
        const status2 = document.getElementById("clip-status");
        if (status2) {
          status2.textContent = `\u{1F4C4} Processing page ${i} of ${totalPages}...`;
          status2.className = "loading";
        }
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        const pageText = textContent.items.map((item) => item.str).join(" ");
        fullText += pageText + "\n";
        logToConsole(`\u2705 Page ${i} processed, text length: ${pageText.length} characters`, "debug");
      }
      logToConsole(`\u{1F389} PDF extraction completed! Total text length: ${fullText.length} characters`, "success");
      resolve(fullText.trim());
    } catch (error) {
      logToConsole(`\u274C Error in PDF library extraction: ${error}`, "error");
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
      throw new Error("Groq API failed");
    }
    throw new Error("Both Groq and Ollama APIs failed");
  }
  async function generateJobReportWithOllama(jobData, resumeContent) {
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
    const ollamaResponse = await callOllamaAPI(prompt2);
    if (ollamaResponse) {
      return ollamaResponse;
    }
    throw new Error("Ollama API failed");
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
