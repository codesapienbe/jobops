// src/popup.ts

// Declare for esbuild global define
// eslint-disable-next-line no-var, @typescript-eslint/no-unused-vars
// @ts-ignore
declare const JOBOPS_BACKEND_URL: string | undefined;

document.addEventListener("DOMContentLoaded", async () => {
  let jobData: Record<string, any> = {};
  const generateBtn = document.getElementById("generate") as HTMLButtonElement;
  // Set backendUrl from env or fallback, then store in chrome.storage.sync
  const backendUrl: string = (typeof JOBOPS_BACKEND_URL !== 'undefined' ? JOBOPS_BACKEND_URL : 'http://localhost:8877');
  chrome.storage.sync.set({ jobops_backend_url: backendUrl }, async () => {
    // Check Ollama availability and show/hide Generate button
    if (generateBtn) {
      const ollamaAvailable = await isOllamaAvailable();
      generateBtn.style.display = ollamaAvailable ? '' : 'none';
    }
    requestJobData();
  });

  // Listen for preview data from content script
  chrome.runtime.onMessage.addListener((msg, _sender, _sendResponse) => {
    if (msg.action === "show_preview" && msg.jobData) {
      jobData = msg.jobData;
      renderPreview(jobData);
    }
  });

  // Request job data from the content script on popup open
  function requestJobData() {
    console.info('[JobOps Clipper] Requesting job data from content script...');
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]?.id) return;
      // First, check if the content script is injected
      chrome.scripting.executeScript(
        {
          target: { tabId: tabs[0].id },
          func: () => !!window && !!window.document && !!window.document.body,
        },
        (results) => {
          if (chrome.runtime.lastError || !results || !results[0].result) {
            (document.getElementById("clip-status") as HTMLElement).textContent =
              "Content script not loaded. Please refresh the page and try again.";
            return;
          }
          // Now send the message
          chrome.tabs.sendMessage(
            tabs[0].id!,
            { action: "clip_page" },
            (response) => {
              if (chrome.runtime.lastError) {
                (document.getElementById("clip-status") as HTMLElement).textContent =
                  "Could not connect to content script. Try refreshing the page.";
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

  (document.getElementById("approve") as HTMLButtonElement).onclick = async () => {
    if (!jobData || Object.keys(jobData).length === 0) return;
    const jsonString = JSON.stringify(jobData, null, 2);
    try {
      await navigator.clipboard.writeText(jsonString);
      (document.getElementById("clip-status") as HTMLElement).textContent = "Copied to clipboard!";
      setTimeout(() => window.close(), 1200);
    } catch (e) {
      (document.getElementById("clip-status") as HTMLElement).textContent = "Failed to copy to clipboard.";
    }
    // Removed: enhanceWithOllama call from here
  };

  (document.getElementById("generate") as HTMLButtonElement).onclick = async () => {
    const generateBtn = document.getElementById("generate") as HTMLButtonElement;
    const status = document.getElementById("clip-status") as HTMLElement;
    const progressBar = document.getElementById("progress-bar") as HTMLElement;
    if (!jobData || Object.keys(jobData).length === 0) return;
    generateBtn.disabled = true;
    status.textContent = "Checking Ollama model...";
    progressBar.style.display = "block";
    try {
      const modelAvailable = await isOllamaModelAvailable(OLLAMA_MODEL);
      if (!modelAvailable) {
        status.textContent = `Ollama model '${OLLAMA_MODEL}' is not available. Please pull it with 'ollama pull ${OLLAMA_MODEL}' and try again.`;
        progressBar.style.display = "none";
        generateBtn.disabled = false;
        return;
      }
      status.textContent = "Generating structured data...";
      const enhanced = await enhanceWithOllama(jobData);
      jobData = enhanced;
      renderPreview(jobData);
      status.textContent = "Structured data generated.";
    } catch (e: any) {
      status.textContent = "Failed to generate structured data: " + (e?.message || e);
    } finally {
      progressBar.style.display = "none";
      generateBtn.disabled = false;
    }
  };

  (document.getElementById("cancel") as HTMLButtonElement).onclick = () => window.close();
});

function renderPreview(jobData: Record<string, any>) {
  const container = document.getElementById("preview-container") || document.createElement("div");
  container.id = "preview-container";
  let html = '<div class="jobops-preview-table">';
  for (const [key, value] of Object.entries(jobData)) {
    if (key === 'headings' && Array.isArray(value)) {
      html += `<div class="preview-row"><span class="preview-key">${escapeHtml(key)}</span><span class="preview-value">`;
      if (value.length === 0) {
        html += '<span class="tag-empty">(none)</span>';
      } else {
        for (const heading of value) {
          html += `<span class="heading-tag">${escapeHtml(heading.text)} <span class="heading-tag-type">${escapeHtml(heading.tag)}</span></span> `;
        }
      }
      html += '</span></div>';
    } else if (key === 'images' && Array.isArray(value)) {
      html += `<div class="preview-row"><span class="preview-key">${escapeHtml(key)}</span><span class="preview-value images-row">`;
      if (value.length === 0) {
        html += '<span class="tag-empty">(none)</span>';
      } else {
        for (const img of value) {
          html += `<img class="preview-img-thumb" src="${escapeHtml(img.src)}" alt="${escapeHtml(img.alt || '')}" title="${escapeHtml(img.alt || img.src)}" loading="lazy" />`;
        }
      }
      html += '</span></div>';
    } else {
      html += `<div class="preview-row"><span class="preview-key">${escapeHtml(key)}</span><span class="preview-value">${escapeHtml(Array.isArray(value) || typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value))}</span></div>`;
    }
  }
  html += '</div>';
  container.innerHTML = html;
  // Replace or append preview
  const parent = document.querySelector(".glassmorphic-popup") || document.body;
  let old = document.getElementById("preview-container");
  if (old) old.replaceWith(container); else parent.insertBefore(container, parent.firstChild);
}

// Escape HTML for safe pre display
function escapeHtml(str: string): string {
  return str.replace(/[&<>"']/g, function (c) {
    return ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;','\'':'&#39;'})[c] || c;
  });
}

// Ollama enhancement helper
const OLLAMA_URL = 'http://localhost:11434';
const OLLAMA_MODEL = 'qwen3:1.7b';
async function enhanceWithOllama(jobData: Record<string, any>): Promise<Record<string, any>> {
  const prompt = `Given the following job data as JSON, extract as much structured information as possible, filling in missing fields (e.g., description, tags, summary, company, skills, etc.) and returning a completed JSON.\n\n${JSON.stringify(jobData, null, 2)}`;
  console.info('[JobOps Clipper] Sending prompt to Ollama:', prompt);
  const response = await fetch(`${OLLAMA_URL}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: OLLAMA_MODEL,
      prompt,
      stream: false
    })
  });
  if (!response.ok) {
    let errorMsg = 'Ollama API error';
    try {
      const err = await response.json();
      if (err.error) errorMsg = err.error;
      else if (err.message) errorMsg = err.message;
      else errorMsg = JSON.stringify(err);
    } catch (e) {
      try {
        const text = await response.text();
        if (text) errorMsg = text;
      } catch {}
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

async function isOllamaModelAvailable(model: string): Promise<boolean> {
  try {
    const response = await fetch(`${OLLAMA_URL}/api/tags`);
    if (!response.ok) return false;
    const data = await response.json();
    if (!data.models || !Array.isArray(data.models)) return false;
    return data.models.some((m: any) => m.name === model);
  } catch {
    return false;
  }
}

async function isOllamaAvailable(): Promise<boolean> {
  try {
    const response = await fetch(`${OLLAMA_URL}/api/tags`);
    return response.ok;
  } catch {
    return false;
  }
}
