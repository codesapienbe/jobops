"use strict";
(() => {
  // src/popup.ts
  var GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions";
  var GROQ_MODEL = "qwen2.5-32b-instant";
  var OLLAMA_URL = "http://localhost:11434";
  var OLLAMA_MODEL = "qwen3:1.7b";
  var consoleOutput = null;
  var isGenerating = false;
  var abortController = null;
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
    const realtimeResponse = document.getElementById("realtime-response");
    const stopGenerationBtn = document.getElementById("stop-generation");
    const copyRealtimeBtn = document.getElementById("copy-realtime");
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
    logToConsole("\u2705 Generate Report button enabled and ready", "success");
    generateReportBtn.style.opacity = "1";
    generateReportBtn.style.cursor = "pointer";
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
    generateReportBtn.addEventListener("click", (event) => {
      console.log("\u{1F3AF} GENERATE REPORT BUTTON CLICKED - DIRECT CONSOLE LOG");
      logToConsole("\u{1F3AF} Generate Report button clicked - event handler triggered", "info");
      generateReportBtn.style.transform = "scale(0.95)";
      setTimeout(() => {
        generateReportBtn.style.transform = "scale(1)";
      }, 100);
      handleGenerateReport();
    });
    settingsBtn.addEventListener("click", handleSettings);
    settingsBtn.addEventListener("contextmenu", handleTestAPI);
    if (clearConsoleBtn) {
      clearConsoleBtn.addEventListener("click", clearConsole);
    }
    if (stopGenerationBtn) {
      stopGenerationBtn.addEventListener("click", handleStopGeneration);
    }
    if (copyRealtimeBtn) {
      copyRealtimeBtn.addEventListener("click", handleCopyRealtime);
    }
    logToConsole("\u{1F680} JobOps Clipper initialized", "info");
    logToConsole("\u{1F4CB} Ready to process job postings and resumes", "success");
    function setupToggleHandlers() {
      const toggleHeaders = document.querySelectorAll(".properties-header, .markdown-header, .realtime-header");
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
      if (!content) {
        logToConsole(`\u274C Section element not found: ${sectionId}`, "error");
        return;
      }
      const header = content.parentElement?.querySelector('[data-toggle="' + sectionId + '"]');
      const toggleIcon = header?.querySelector(".toggle-icon");
      if (content && header && toggleIcon) {
        const isCollapsed = content.classList.contains("collapsed");
        if (isCollapsed) {
          content.classList.remove("collapsed");
          content.classList.add("expanded");
          toggleIcon.textContent = "\u25BC";
          logToConsole(`\u2705 Section expanded: ${sectionId}`, "debug");
        } else {
          content.classList.remove("expanded");
          content.classList.add("collapsed");
          toggleIcon.textContent = "\u25B6";
          logToConsole(`\u2705 Section collapsed: ${sectionId}`, "debug");
        }
      } else {
        logToConsole(`\u274C Header or toggle icon not found for section: ${sectionId}`, "error");
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
        const imageCount = document.createElement("div");
        imageCount.className = "property-image-count";
        imageCount.textContent = `\u{1F5BC}\uFE0F ${data.images.length} images (not loaded)`;
        imageCount.title = "Images skipped for performance";
        propImages.appendChild(imageCount);
        logToConsole(`\u{1F5BC}\uFE0F Skipped loading ${data.images.length} images for generate-report workflow`, "info");
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
                  logToConsole(`\u{1F4CB} Job data keys: ${Object.keys(response.jobData).join(", ")}`, "debug");
                  if (!response.jobData.title && !response.jobData.body) {
                    logToConsole("\u26A0\uFE0F Job data missing essential fields (title/body)", "warning");
                    showNotification2("\u26A0\uFE0F Job data incomplete. Please refresh the page and try again.", true);
                    return;
                  }
                  jobData = response.jobData;
                  populatePropertyFields(jobData);
                  markdownEditor.value = generateMarkdown(jobData);
                  copyBtn.disabled = false;
                  logToConsole("\u2705 Job data populated successfully", "success");
                } else {
                  logToConsole("\u26A0\uFE0F No job data received from content script", "warning");
                  showNotification2("\u26A0\uFE0F No job data found. Please refresh the page and try again.", true);
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
          showNotification2("No content to copy!", true);
          return;
        }
        logToConsole(`\u{1F4CB} Copying content (${contentToCopy.length} characters) to clipboard...`, "progress");
        await navigator.clipboard.writeText(contentToCopy);
        logToConsole("\u2705 Content copied to clipboard successfully!", "success");
        showNotification2("\u2705 Content copied to clipboard!");
        status.textContent = "Copied to clipboard!";
        setTimeout(() => status.textContent = "", 2e3);
      } catch (e) {
        logToConsole(`\u274C Copy failed: ${e}`, "error");
        showNotification2("\u274C Failed to copy to clipboard", true);
        status.textContent = "Failed to copy to clipboard.";
      }
    };
    function showNotification2(message, isError = false) {
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
      console.log("\u{1F3AF} RESUME UPLOAD TRIGGERED - DIRECT CONSOLE LOG");
      logToConsole("\u{1F4C1} Resume upload triggered", "info");
      const target = event.target;
      const file = target.files?.[0];
      if (!file) {
        logToConsole("\u274C No file selected", "error");
        showNotification2("No file selected", true);
        return;
      }
      if (file.type !== "application/pdf") {
        logToConsole("\u274C Invalid file type - PDF required", "error");
        showNotification2("Please select a PDF file", true);
        return;
      }
      logToConsole(`\u{1F4C4} Starting PDF extraction: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, "progress");
      try {
        status.textContent = "\u{1F4C4} Loading PDF file...";
        status.className = "loading";
        showNotification2("\u{1F4C4} Loading PDF file...");
        logToConsole("\u{1F4C4} Loading PDF file into memory...", "progress");
        status.textContent = "\u{1F50D} Extracting text content from PDF...";
        status.className = "loading";
        showNotification2("\u{1F50D} Extracting PDF content...");
        logToConsole("\u{1F50D} Extracting text content from PDF...", "progress");
        console.log("\u{1F3AF} ABOUT TO EXTRACT PDF CONTENT - DIRECT CONSOLE LOG");
        resumeContent = await extractPdfContent(file);
        console.log("\u{1F3AF} PDF EXTRACTION COMPLETED - DIRECT CONSOLE LOG");
        logToConsole(`\u2705 PDF extraction completed! Content length: ${resumeContent.length} characters`, "success");
        logToConsole(`\u{1F4C4} Resume content preview: ${resumeContent.substring(0, 200)}${resumeContent.length > 200 ? "..." : ""}`, "debug");
        logToConsole(`\u{1F4C4} Resume content stored in variable: ${resumeContent ? "YES" : "NO"}`, "debug");
        status.textContent = "\u2705 Resume content extracted successfully!";
        status.className = "success";
        showNotification2("\u2705 Resume content extracted successfully!");
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
        showNotification2(`\u274C Failed to extract PDF content: ${errorMessage}`, true);
      }
    }
    async function handleGenerateReport() {
      console.log("\u{1F3AF} GENERATE REPORT BUTTON CLICKED - DIRECT CONSOLE LOG");
      logToConsole("\u{1F680} Generate Report button clicked", "info");
      logToConsole(`\u{1F4CA} Current resumeContent length: ${resumeContent.length}`, "debug");
      logToConsole(`\u{1F4CB} Current jobData keys: ${Object.keys(jobData).join(", ")}`, "debug");
      if (!resumeContent) {
        logToConsole("\u{1F4C1} No resume content found, triggering file upload", "warning");
        resumeUpload.click();
        return;
      }
      if (!jobData || Object.keys(jobData).length === 0) {
        logToConsole("\u{1F4CB} No job data found, requesting from current page", "warning");
        await new Promise((resolve) => {
          requestJobData();
          setTimeout(() => {
            logToConsole(`\u{1F4CB} After requestJobData - jobData keys: ${Object.keys(jobData).join(", ")}`, "debug");
            logToConsole(`\u{1F4CB} Job data title: ${jobData.title || "N/A"}`, "debug");
            logToConsole(`\u{1F4CB} Job data body length: ${jobData.body ? jobData.body.length : 0}`, "debug");
            resolve();
          }, 1e3);
        });
        if (!jobData || Object.keys(jobData).length === 0) {
          logToConsole("\u274C Still no job data after request, cannot proceed", "error");
          showNotification2("\u274C No job data available. Please refresh the page and try again.", true);
          return;
        }
      }
      if (!jobData.title && !jobData.body) {
        logToConsole("\u274C Job data missing essential fields (title/body)", "error");
        showNotification2("\u274C Job data incomplete. Please refresh the page and try again.", true);
        return;
      }
      logToConsole("\u{1F680} Starting report generation process", "info");
      generateReportBtn.disabled = true;
      status.textContent = "\u{1F504} Starting report generation...";
      status.className = "loading";
      showNotification2("\u{1F504} Starting report generation...");
      logToConsole("\u{1F3AF} BUTTON CLICK VERIFICATION - This should appear immediately", "info");
      try {
        logToConsole("\u{1F511} Checking API configuration...", "progress");
        status.textContent = "\u{1F511} Checking API configuration...";
        status.className = "loading";
        const apiKey = await getGroqApiKey();
        if (!apiKey) {
          throw new Error("Groq API key not configured");
        }
        logToConsole("\u2705 API key found, proceeding with report generation", "success");
        showNotification2("\u2705 API key found, proceeding...");
        logToConsole("\u{1F4CA} Preparing job data and resume content...", "progress");
        logToConsole(`\u{1F4CB} Job data keys: ${Object.keys(jobData).join(", ")}`, "debug");
        logToConsole(`\u{1F4C4} Resume content length: ${resumeContent.length} characters`, "debug");
        status.textContent = "\u{1F4CA} Preparing job data and resume content...";
        status.className = "loading";
        showNotification2("\u{1F4CA} Preparing data for analysis...");
        logToConsole("\u{1F916} Starting streaming report generation...", "progress");
        status.textContent = "\u{1F916} Starting streaming report generation...";
        status.className = "loading";
        showNotification2("\u{1F916} Starting streaming analysis...");
        logToConsole("\u{1F527} Forcing real-time section expansion...", "debug");
        const realtimeContent = document.getElementById("realtime-content");
        if (realtimeContent) {
          if (realtimeContent.classList.contains("collapsed")) {
            toggleSection("realtime-content");
            logToConsole("\u2705 Real-time section expanded", "debug");
          } else {
            logToConsole("\u2705 Real-time section already expanded", "debug");
          }
        } else {
          logToConsole("\u274C Real-time content element not found", "error");
        }
        const realtimeResponse2 = document.getElementById("realtime-response");
        if (realtimeResponse2) {
          realtimeResponse2.innerHTML = '<span class="typing-text">\u{1F680} Starting report generation...</span>';
          realtimeResponse2.classList.add("typing");
          logToConsole("\u2705 Real-time response element initialized with test message", "debug");
        } else {
          logToConsole("\u274C Real-time response element not found", "error");
        }
        if (stopGenerationBtn) {
          stopGenerationBtn.style.display = "inline-block";
          logToConsole("\u2705 Stop generation button shown", "debug");
        } else {
          logToConsole("\u274C Stop generation button not found", "error");
        }
        isGenerating = true;
        abortController = new AbortController();
        logToConsole("\u{1F504} Calling generateJobReportStreaming...", "debug");
        const report = await generateJobReportStreaming(jobData, resumeContent, (chunk) => {
          logToConsole(`\u{1F4DD} Chunk callback received: ${chunk.length} characters`, "debug");
          const realtimeResponse3 = document.getElementById("realtime-response");
          if (realtimeResponse3) {
            const span = document.createElement("span");
            span.className = "typing-text";
            span.textContent = chunk;
            realtimeResponse3.appendChild(span);
            realtimeResponse3.scrollTop = realtimeResponse3.scrollHeight;
            logToConsole(`\u{1F4DD} Real-time chunk added to UI: ${chunk.length} characters`, "debug");
          } else {
            logToConsole("\u274C Real-time response element not found in chunk callback", "error");
          }
        });
        logToConsole(`\u{1F4CA} Report generation result: ${report ? "success" : "failed"}`, "debug");
        if (!report) {
          throw new Error("No report generated - API returned empty response");
        }
        logToConsole("\u2705 Report generated successfully!", "success");
        status.textContent = "\u2705 Report generated successfully!";
        status.className = "success";
        showNotification2("\u2705 Report generated successfully!");
        markdownEditor.value = report;
        if (realtimeResponse2) {
          realtimeResponse2.classList.remove("typing");
          logToConsole("\u2705 Real-time response completed", "success");
        }
        setTimeout(() => {
          status.textContent = "\u{1F4CB} Report ready - use Copy button to copy content";
          status.className = "success";
          logToConsole("\u{1F4CB} Report ready for copying", "success");
        }, 2e3);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logToConsole(`\u274C Report generation failed: ${errorMessage}`, "error");
        isGenerating = false;
        abortController = null;
        const realtimeResponse2 = document.getElementById("realtime-response");
        if (realtimeResponse2) {
          realtimeResponse2.classList.remove("typing");
          realtimeResponse2.innerHTML += `<br><span style="color: #ff6b6b;">\u274C Error: ${errorMessage}</span>`;
          logToConsole("\u2705 Error message added to real-time response", "debug");
        }
        if (stopGenerationBtn) {
          stopGenerationBtn.style.display = "none";
        }
        if (errorMessage.includes("API key")) {
          logToConsole("\u{1F527} API key required - please configure in settings", "warning");
          status.textContent = "\u274C API key required - click \u2699\uFE0F to configure";
          status.className = "error";
          showNotification2("\u274C Groq API key not configured. Click \u2699\uFE0F to set it up.", true);
        } else if (errorMessage.includes("Groq API")) {
          logToConsole("\u26A0\uFE0F Groq API failed, trying Ollama fallback...", "warning");
          status.textContent = "\u26A0\uFE0F Groq API failed, trying Ollama fallback...";
          status.className = "loading";
          showNotification2("\u26A0\uFE0F Groq API failed, trying Ollama...");
          try {
            logToConsole("\u{1F504} Attempting Ollama fallback...", "progress");
            status.textContent = "\u{1F504} Attempting Ollama fallback...";
            status.className = "loading";
            const report = await generateJobReportWithOllama(jobData, resumeContent);
            markdownEditor.value = report;
            logToConsole("\u2705 Report generated with Ollama fallback!", "success");
            status.textContent = "\u2705 Report generated with Ollama!";
            status.className = "success";
            showNotification2("\u2705 Report generated with Ollama fallback!");
          } catch (ollamaError) {
            logToConsole("\u274C Both Groq and Ollama failed", "error");
            status.textContent = "\u274C Both Groq and Ollama failed";
            status.className = "error";
            showNotification2("\u274C Report generation failed on all services", true);
          }
        } else {
          logToConsole("\u274C Report generation failed with unknown error", "error");
          status.textContent = "\u274C Report generation failed";
          status.className = "error";
          showNotification2("\u274C Report generation failed", true);
        }
      } finally {
        generateReportBtn.disabled = false;
        isGenerating = false;
        abortController = null;
        if (realtimeResponse) {
          realtimeResponse.classList.remove("typing");
        }
        if (stopGenerationBtn) {
          stopGenerationBtn.style.display = "none";
        }
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
              showNotification2("\u2705 Groq API key saved!");
              resolve();
            });
          });
        } else {
          logToConsole("\u{1F5D1}\uFE0F Removing Groq API key...", "warning");
          await new Promise((resolve) => {
            chrome.storage.sync.remove(["groq_api_key"], () => {
              logToConsole("\u2705 Groq API key removed successfully!", "success");
              showNotification2("\u2705 Groq API key removed!");
              resolve();
            });
          });
        }
      } else {
        logToConsole("\u274C Settings dialog cancelled", "info");
      }
    }
    async function handleTestAPI(event) {
      event.preventDefault();
      logToConsole("\u{1F9EA} Testing API connectivity...", "info");
      try {
        const apiKey = await getGroqApiKey();
        if (!apiKey) {
          logToConsole("\u274C No API key configured", "error");
          showNotification2("\u274C No API key configured", true);
          return;
        }
        logToConsole("\u{1F511} API key found, testing Groq API...", "progress");
        const testResponse = await callGroqAPI("Say 'Hello, API test successful!'", (chunk) => {
          logToConsole(`\u{1F9EA} Test chunk: ${chunk}`, "debug");
        });
        if (testResponse) {
          logToConsole("\u2705 API test successful!", "success");
          showNotification2("\u2705 API test successful!");
        } else {
          logToConsole("\u274C API test failed - no response", "error");
          showNotification2("\u274C API test failed", true);
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logToConsole(`\u274C API test failed: ${errorMessage}`, "error");
        showNotification2(`\u274C API test failed: ${errorMessage}`, true);
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
          const header = new TextDecoder().decode(typedarray.slice(0, 10));
          logToConsole(`\u{1F4C4} File header: ${header}`, "debug");
          if (!header.includes("%PDF")) {
            logToConsole("\u26A0\uFE0F File doesn't appear to be a valid PDF", "warning");
          }
          try {
            const pdfjsLib = window["pdfjs-dist/build/pdf"];
            if (pdfjsLib) {
              logToConsole("\u2705 PDF.js available, using it for extraction...", "success");
              extractPdfWithLibrary(typedarray, resolve, reject);
              return;
            }
          } catch (error) {
            logToConsole(`\u26A0\uFE0F PDF.js method failed: ${error}`, "warning");
          }
          logToConsole("\u{1F4DA} PDF.js not available, trying to load from multiple sources...", "progress");
          const status = document.getElementById("clip-status");
          if (status) {
            status.textContent = "\u{1F4DA} Loading PDF processing library...";
            status.className = "loading";
          }
          const cdnSources = [
            "https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.min.js",
            "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js",
            "https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.min.js"
          ];
          let loaded = false;
          const timeout = setTimeout(() => {
            if (!loaded) {
              logToConsole("\u23F0 PDF.js loading timeout, using fallback method", "warning");
              const fallbackText = extractPdfFallback(typedarray);
              if (fallbackText && fallbackText.length > 50) {
                resolve(fallbackText);
              } else {
                const manualText = prompt("PDF extraction failed. Please paste your resume content manually:");
                if (manualText && manualText.trim().length > 10) {
                  resolve(manualText.trim());
                } else {
                  reject(new Error("No resume content available"));
                }
              }
            }
          }, 1e4);
          for (const source of cdnSources) {
            if (loaded)
              break;
            try {
              logToConsole(`\u{1F4DA} Trying to load PDF.js from: ${source}`, "debug");
              const script = document.createElement("script");
              script.src = source;
              script.onload = () => {
                if (!loaded) {
                  loaded = true;
                  clearTimeout(timeout);
                  logToConsole(`\u2705 PDF.js loaded from ${source}`, "success");
                  extractPdfWithLibrary(typedarray, resolve, reject);
                }
              };
              script.onerror = () => {
                logToConsole(`\u274C Failed to load PDF.js from ${source}`, "debug");
              };
              document.head.appendChild(script);
              await new Promise((resolve2) => setTimeout(resolve2, 2e3));
            } catch (error) {
              logToConsole(`\u274C Error loading from ${source}: ${error}`, "debug");
            }
          }
          if (!loaded) {
            logToConsole("\u26A0\uFE0F All PDF.js sources failed, using fallback method...", "warning");
            const fallbackText = extractPdfFallback(typedarray);
            if (fallbackText && fallbackText.length > 50) {
              logToConsole("\u2705 Fallback PDF extraction successful", "success");
              resolve(fallbackText);
            } else {
              logToConsole("\u274C All PDF extraction methods failed, using manual input", "warning");
              const manualText = prompt("PDF extraction failed. Please paste your resume content manually:");
              if (manualText && manualText.trim().length > 10) {
                logToConsole("\u2705 Manual resume content provided", "success");
                resolve(manualText.trim());
              } else {
                logToConsole("\u274C No manual content provided", "error");
                reject(new Error("No resume content available"));
              }
            }
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
  function extractPdfFallback(typedarray) {
    try {
      logToConsole("\u{1F504} Using fallback PDF extraction method...", "progress");
      const decoder = new TextDecoder("utf-8");
      const text = decoder.decode(typedarray);
      const textMatches = text.match(/\(([^)]+)\)/g);
      if (textMatches && textMatches.length > 0) {
        const extractedText = textMatches.map((match) => match.slice(1, -1)).filter((text2) => text2.length > 3 && !text2.match(/^[0-9\s]+$/)).join(" ");
        if (extractedText.length > 50) {
          logToConsole(`\u2705 Fallback extraction found ${extractedText.length} characters`, "success");
          return extractedText;
        }
      }
      const readableText = text.match(/[A-Za-z\s]{10,}/g);
      if (readableText && readableText.length > 0) {
        const combined = readableText.join(" ").trim();
        if (combined.length > 50) {
          logToConsole(`\u2705 Fallback extraction found ${combined.length} characters`, "success");
          return combined;
        }
      }
      logToConsole("\u26A0\uFE0F Fallback extraction found minimal text", "warning");
      return "PDF content could not be extracted. Please ensure the PDF contains text (not just images).";
    } catch (error) {
      logToConsole(`\u274C Fallback extraction failed: ${error}`, "error");
      return "PDF extraction failed. Please try a different PDF file.";
    }
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
  async function generateJobReportStreaming(jobData, resumeContent, onChunk) {
    const cleanJobData = { ...jobData };
    if (cleanJobData.images) {
      delete cleanJobData.images;
    }
    const prompt2 = `You are an expert job application analyst. Based on the provided job posting data and resume content, generate a comprehensive job application tracking report.

Job Posting Data:
${JSON.stringify(cleanJobData, null, 2)}

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
      logToConsole("\u{1F916} Attempting Groq API with streaming...", "progress");
      const groqResponse = await callGroqAPI(prompt2, onChunk);
      if (groqResponse) {
        logToConsole("\u2705 Groq API succeeded with streaming", "success");
        return groqResponse;
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logToConsole(`\u26A0\uFE0F Groq API failed: ${errorMessage}`, "warning");
      logToConsole("\u{1F504} Falling back to Ollama...", "progress");
      try {
        logToConsole("\u{1F916} Attempting Ollama API fallback...", "progress");
        const ollamaResponse = await callOllamaAPI(prompt2);
        if (ollamaResponse) {
          logToConsole("\u2705 Ollama API succeeded", "success");
          return ollamaResponse;
        }
      } catch (ollamaError) {
        const ollamaErrorMessage = ollamaError instanceof Error ? ollamaError.message : String(ollamaError);
        logToConsole(`\u274C Ollama API also failed: ${ollamaErrorMessage}`, "error");
      }
    }
    logToConsole("\u274C Both Groq and Ollama APIs failed", "error");
    throw new Error("Both Groq and Ollama APIs failed");
  }
  async function generateJobReportWithOllama(jobData, resumeContent) {
    const cleanJobData = { ...jobData };
    if (cleanJobData.images) {
      delete cleanJobData.images;
    }
    const prompt2 = `You are an expert job application analyst. Based on the provided job posting data and resume content, generate a comprehensive job application tracking report.

Job Posting Data:
${JSON.stringify(cleanJobData, null, 2)}

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
  async function callGroqAPI(prompt2, onChunk) {
    try {
      logToConsole("\u{1F511} Retrieving Groq API key from storage...", "debug");
      const apiKey = await getGroqApiKey();
      if (!apiKey) {
        logToConsole("\u274C No Groq API key found in storage", "error");
        throw new Error("Groq API key not configured");
      }
      logToConsole("\u2705 Groq API key retrieved successfully", "debug");
      logToConsole(`\u{1F310} Preparing request to Groq API: ${GROQ_API_URL}`, "debug");
      logToConsole(`\u{1F916} Using model: ${GROQ_MODEL}`, "debug");
      logToConsole(`\u{1F4DD} Prompt length: ${prompt2.length} characters`, "debug");
      const requestBody = {
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
        stream: onChunk ? true : false
      };
      logToConsole("\u{1F4E4} Sending request to Groq API...", "debug");
      logToConsole(`\u{1F4CA} Request payload size: ${JSON.stringify(requestBody).length} characters`, "debug");
      logToConsole(`\u{1F504} Streaming mode: ${onChunk ? "enabled" : "disabled"}`, "debug");
      const startTime = Date.now();
      const response = await fetch(GROQ_API_URL, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${apiKey}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(requestBody),
        signal: abortController?.signal
      });
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      logToConsole(`\u23F1\uFE0F Response received in ${responseTime}ms`, "debug");
      logToConsole(`\u{1F4E1} HTTP Status: ${response.status} ${response.statusText}`, "debug");
      logToConsole(`\u{1F4CB} Response headers: ${JSON.stringify(Object.fromEntries(response.headers.entries()))}`, "debug");
      if (!response.ok) {
        const errorText = await response.text();
        logToConsole(`\u274C Groq API error response: ${errorText}`, "error");
        throw new Error(`Groq API error: ${response.status} ${response.statusText} - ${errorText}`);
      }
      if (onChunk && requestBody.stream) {
        logToConsole("\u{1F504} Processing streaming response...", "debug");
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let fullResponse = "";
        if (!reader) {
          throw new Error("Response body reader not available");
        }
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done)
              break;
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split("\n");
            for (const line of lines) {
              if (line.startsWith("data: ")) {
                const data = line.slice(6);
                if (data === "[DONE]") {
                  logToConsole("\u2705 Streaming completed", "success");
                  return fullResponse;
                }
                try {
                  const parsed = JSON.parse(data);
                  if (parsed.choices && parsed.choices[0]?.delta?.content) {
                    const content = parsed.choices[0].delta.content;
                    fullResponse += content;
                    onChunk(content);
                    logToConsole(`\u{1F4DD} Streamed chunk: ${content.length} characters`, "debug");
                  }
                } catch (e) {
                  logToConsole(`\u26A0\uFE0F Ignoring malformed chunk: ${e}`, "debug");
                }
              }
            }
          }
          logToConsole(`\u2705 Streaming completed, total: ${fullResponse.length} characters`, "success");
          return fullResponse;
        } finally {
          reader.releaseLock();
        }
      } else {
        logToConsole("\u{1F4E5} Processing non-streaming response...", "debug");
        const data = await response.json();
        logToConsole(`\u{1F4CA} Response data keys: ${Object.keys(data).join(", ")}`, "debug");
        logToConsole(`\u{1F3AF} Choices count: ${data.choices?.length || 0}`, "debug");
        if (data.choices && data.choices.length > 0) {
          const content = data.choices[0]?.message?.content;
          if (content) {
            logToConsole(`\u2705 Successfully extracted response content (${content.length} characters)`, "success");
            logToConsole(`\u{1F4DD} Response preview: ${content.substring(0, 200)}${content.length > 200 ? "..." : ""}`, "debug");
            return content;
          } else {
            logToConsole("\u26A0\uFE0F Response content is empty or undefined", "warning");
            logToConsole(`\u{1F50D} Full response structure: ${JSON.stringify(data, null, 2)}`, "debug");
            return null;
          }
        } else {
          logToConsole("\u26A0\uFE0F No choices found in response", "warning");
          logToConsole(`\u{1F50D} Full response structure: ${JSON.stringify(data, null, 2)}`, "debug");
          return null;
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      const errorStack = error instanceof Error ? error.stack : "No stack trace available";
      logToConsole(`\u274C Groq API call failed: ${errorMessage}`, "error");
      logToConsole(`\u{1F50D} Error stack trace: ${errorStack}`, "debug");
      if (error instanceof TypeError && error.message.includes("fetch")) {
        logToConsole("\u{1F310} Network error detected - check internet connection", "error");
      } else if (error instanceof SyntaxError) {
        logToConsole("\u{1F4DD} JSON parsing error - invalid response format", "error");
      }
      return null;
    }
  }
  async function callOllamaAPI(prompt2) {
    try {
      logToConsole("\u{1F504} Preparing Ollama API fallback request...", "debug");
      logToConsole(`\u{1F310} Ollama URL: ${OLLAMA_URL}/api/generate`, "debug");
      logToConsole(`\u{1F916} Using model: ${OLLAMA_MODEL}`, "debug");
      logToConsole(`\u{1F4DD} Prompt length: ${prompt2.length} characters`, "debug");
      const requestBody = {
        model: OLLAMA_MODEL,
        prompt: prompt2,
        stream: false
      };
      logToConsole("\u{1F4E4} Sending request to Ollama API...", "debug");
      logToConsole(`\u{1F4CA} Request payload size: ${JSON.stringify(requestBody).length} characters`, "debug");
      const startTime = Date.now();
      const response = await fetch(`${OLLAMA_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody)
      });
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      logToConsole(`\u23F1\uFE0F Ollama response received in ${responseTime}ms`, "debug");
      logToConsole(`\u{1F4E1} HTTP Status: ${response.status} ${response.statusText}`, "debug");
      logToConsole(`\u{1F4CB} Response headers: ${JSON.stringify(Object.fromEntries(response.headers.entries()))}`, "debug");
      if (!response.ok) {
        const errorText = await response.text();
        logToConsole(`\u274C Ollama API error response: ${errorText}`, "error");
        throw new Error(`Ollama API error: ${response.status} ${response.statusText} - ${errorText}`);
      }
      logToConsole("\u{1F4E5} Parsing Ollama JSON response...", "debug");
      const data = await response.json();
      logToConsole(`\u{1F4CA} Ollama response data keys: ${Object.keys(data).join(", ")}`, "debug");
      if (data.response) {
        logToConsole(`\u2705 Successfully extracted Ollama response content (${data.response.length} characters)`, "success");
        logToConsole(`\u{1F4DD} Ollama response preview: ${data.response.substring(0, 200)}${data.response.length > 200 ? "..." : ""}`, "debug");
        return data.response;
      } else {
        logToConsole("\u26A0\uFE0F Ollama response content is empty or undefined", "warning");
        logToConsole(`\u{1F50D} Full Ollama response structure: ${JSON.stringify(data, null, 2)}`, "debug");
        return null;
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      const errorStack = error instanceof Error ? error.stack : "No stack trace available";
      logToConsole(`\u274C Ollama API call failed: ${errorMessage}`, "error");
      logToConsole(`\u{1F50D} Ollama error stack trace: ${errorStack}`, "debug");
      if (error instanceof TypeError && error.message.includes("fetch")) {
        logToConsole("\u{1F310} Ollama network error detected - check if Ollama is running locally", "error");
      } else if (error instanceof SyntaxError) {
        logToConsole("\u{1F4DD} Ollama JSON parsing error - invalid response format", "error");
      }
      return null;
    }
  }
  async function getGroqApiKey() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(["groq_api_key"], (result) => {
        const apiKey = result.groq_api_key || null;
        if (apiKey) {
          logToConsole(`\u{1F511} API key found (${apiKey.substring(0, 8)}...)`, "debug");
        } else {
          logToConsole("\u274C No API key found in storage", "debug");
        }
        resolve(apiKey);
      });
    });
  }
  function handleStopGeneration() {
    if (abortController) {
      logToConsole("\u23F9\uFE0F Stopping generation...", "warning");
      abortController.abort();
      isGenerating = false;
      abortController = null;
      const stopGenerationBtn = document.getElementById("stop-generation");
      const realtimeResponse = document.getElementById("realtime-response");
      if (stopGenerationBtn) {
        stopGenerationBtn.style.display = "none";
      }
      if (realtimeResponse) {
        realtimeResponse.classList.remove("typing");
      }
      logToConsole("\u2705 Generation stopped", "info");
      showNotification("Generation stopped");
    }
  }
  async function handleCopyRealtime() {
    const realtimeResponse = document.getElementById("realtime-response");
    if (!realtimeResponse || !realtimeResponse.textContent) {
      logToConsole("\u274C No real-time content to copy", "error");
      showNotification("No content to copy!", true);
      return;
    }
    try {
      await navigator.clipboard.writeText(realtimeResponse.textContent);
      logToConsole("\u2705 Real-time response copied to clipboard", "success");
      showNotification("Real-time response copied!");
    } catch (error) {
      logToConsole(`\u274C Failed to copy real-time response: ${error}`, "error");
      showNotification("Failed to copy real-time response", true);
    }
  }
})();
