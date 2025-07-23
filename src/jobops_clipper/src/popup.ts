// src/popup.ts

// Declare for esbuild global define
// eslint-disable-next-line no-var, @typescript-eslint/no-unused-vars
// @ts-ignore
declare const JOBOPS_BACKEND_URL: string | undefined;

document.addEventListener("DOMContentLoaded", async () => {
  let jobData: Record<string, any> = {};
  const generateBtn = document.getElementById("generate") as HTMLButtonElement;
  const refreshBtn = document.getElementById("refresh-ollama") as HTMLButtonElement;
  const status = document.getElementById("clip-status") as HTMLElement;
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

  if (refreshBtn) {
    refreshBtn.onclick = async () => {
      refreshBtn.disabled = true;
      status.textContent = 'Checking Ollama status...';
      const ollamaAvailable = await isOllamaAvailable();
      if (generateBtn) generateBtn.style.display = ollamaAvailable ? '' : 'none';
      status.textContent = ollamaAvailable ? 'Ollama is available.' : 'Ollama is NOT available.';
      setTimeout(() => { status.textContent = ''; }, 2000);
      refreshBtn.disabled = false;
    };
  }

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

function renderMarkdown(md: string): string {
  // Very basic: headings, bold, italics, images, links, code, lists
  return md
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<b>$1</b>')
    .replace(/\*(.*?)\*/gim, '<i>$1</i>')
    .replace(/!\[(.*?)\]\((.*?)\)/gim, '<img alt="$1" src="$2" style="max-width:100px;max-height:100px;border-radius:8px;margin:2px 8px 2px 0;vertical-align:middle;" />')
    .replace(/\[(.*?)\]\((.*?)\)/gim, '<a href="$2" target="_blank">$1</a>')
    .replace(/`([^`]+)`/gim, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}

function renderPreview(jobData: Record<string, any>) {
  const container = document.getElementById("preview-container") || document.createElement("div");
  container.id = "preview-container";
  let md = '';
  if (jobData.title) md += `# ${jobData.title}\n`;
  if (jobData.body) md += `\n${jobData.body}\n`;
  if (jobData.metaKeywords && Array.isArray(jobData.metaKeywords) && jobData.metaKeywords.length > 0) {
    md += `\n## Tags\n`;
    md += jobData.metaKeywords.map((kw: string) => ` [32m [1m${kw} [0m`).join(' ');
    md += '\n';
  }
  if (jobData.headings && Array.isArray(jobData.headings) && jobData.headings.length > 0) {
    md += `\n## Headings\n`;
    for (const h of jobData.headings) {
      md += `- <b>${escapeHtml(h.text)}</b> <span style='opacity:0.7;'>(${escapeHtml(h.tag)})</span>\n`;
    }
    md += '\n';
  }
  if (jobData.images && Array.isArray(jobData.images) && jobData.images.length > 0) {
    md += `\n## Images\n`;
    for (const img of jobData.images) {
      md += `![${img.alt || ''}](${img.src}) `;
    }
    md += '\n';
  }
  // Other fields as sections
  const skipKeys = new Set(['title', 'body', 'metaKeywords', 'headings', 'images']);
  for (const [key, value] of Object.entries(jobData)) {
    if (skipKeys.has(key)) continue;
    if (typeof value === 'string' && value.trim() !== '') {
      md += `\n## ${key.charAt(0).toUpperCase() + key.slice(1)}\n${escapeHtml(value)}\n`;
    } else if (Array.isArray(value) && value.length > 0) {
      md += `\n## ${key.charAt(0).toUpperCase() + key.slice(1)}\n`;
      md += value.map(v => `- ${escapeHtml(typeof v === 'string' ? v : JSON.stringify(v))}`).join('\n');
      md += '\n';
    }
  }
  if (jobData.url) md += `\n[Source](${jobData.url})\n`;
  container.innerHTML = `<div class="jobops-markdown-preview">${renderMarkdown(md)}</div>`;
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
// Define the job schema for structured output
const jobSchema = {
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
async function enhanceWithOllama(jobData: Record<string, any>): Promise<Record<string, any>> {
  const prompt = `Extract and complete the following job data as JSON.`;
  console.info('[JobOps Clipper] Sending prompt to Ollama:', prompt, jobData);
  const response = await fetch(`${OLLAMA_URL}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: OLLAMA_MODEL,
      prompt,
      format: jobSchema,
      stream: false,
      data: jobData // Optionally send jobData as context
    })
  });
  if (!response.ok) {
    let errorMsg = 'Ollama API error';
    try {
      const err = await response.json();
      errorMsg += `\nStatus: ${response.status} ${response.statusText}`;
      errorMsg += `\nHeaders: ${JSON.stringify(Object.fromEntries(response.headers.entries()))}`;
      errorMsg += `\nBody: ${JSON.stringify(err)}`;
      console.error('[JobOps Clipper] Ollama API error:', errorMsg);
    } catch (e) {
      try {
        const text = await response.text();
        errorMsg += `\nStatus: ${response.status} ${response.statusText}`;
        errorMsg += `\nHeaders: ${JSON.stringify(Object.fromEntries(response.headers.entries()))}`;
        errorMsg += `\nBody: ${text}`;
        console.error('[JobOps Clipper] Ollama API error:', errorMsg);
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

