// src/popup.ts

// Declare for esbuild global define
// eslint-disable-next-line no-var, @typescript-eslint/no-unused-vars
// @ts-ignore
declare const JOBOPS_BACKEND_URL: string | undefined;

document.addEventListener("DOMContentLoaded", async () => {
  let jobData: Record<string, any> = {};
  const markdownEditor = document.getElementById("markdown-editor") as HTMLTextAreaElement;
  const copyBtn = document.getElementById("copy-markdown") as HTMLButtonElement;
  const status = document.getElementById("clip-status") as HTMLElement;
  // Property fields
  const propTitle = document.getElementById("prop-title") as HTMLInputElement;
  const propUrl = document.getElementById("prop-url") as HTMLInputElement;
  const propAuthor = document.getElementById("prop-author") as HTMLInputElement;
  const propPublished = document.getElementById("prop-published") as HTMLInputElement;
  const propCreated = document.getElementById("prop-created") as HTMLInputElement;
  const propDescription = document.getElementById("prop-description") as HTMLInputElement;
  const propTags = document.getElementById("prop-tags") as HTMLInputElement;

  // Set backendUrl from env or fallback, then store in chrome.storage.sync
  const backendUrl: string = (typeof JOBOPS_BACKEND_URL !== 'undefined' ? JOBOPS_BACKEND_URL : 'http://localhost:8877');
  chrome.storage.sync.set({ jobops_backend_url: backendUrl }, async () => {
    requestJobData();
  });

  // Listen for preview data from content script
  chrome.runtime.onMessage.addListener((msg, _sender, _sendResponse) => {
    if (msg.action === "show_preview" && msg.jobData) {
      jobData = msg.jobData;
      populatePropertyFields(jobData);
      markdownEditor.value = generateMarkdown(jobData);
    }
  });

  function populatePropertyFields(data: Record<string, any>) {
    propTitle.value = data.title || '';
    propUrl.value = data.url || '';
    propAuthor.value = data.author || '';
    propPublished.value = data.published || '';
    propCreated.value = data.created_at || '';
    propDescription.value = data.description || '';
    propTags.value = Array.isArray(data.metaKeywords) ? data.metaKeywords.join(', ') : (data.metaKeywords || '');
  }

  function updateJobDataFromFields() {
    jobData.title = propTitle.value;
    jobData.url = propUrl.value;
    jobData.author = propAuthor.value;
    jobData.published = propPublished.value;
    jobData.created_at = propCreated.value;
    jobData.description = propDescription.value;
    jobData.metaKeywords = propTags.value.split(',').map(t => t.trim()).filter(Boolean);
    markdownEditor.value = generateMarkdown(jobData);
  }

  [propTitle, propUrl, propAuthor, propPublished, propCreated, propDescription, propTags].forEach(input => {
    input.addEventListener('input', updateJobDataFromFields);
  });

  function requestJobData() {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]?.id) return;
      chrome.scripting.executeScript(
        {
          target: { tabId: tabs[0].id },
          func: () => !!window && !!window.document && !!window.document.body,
        },
        (results) => {
          if (chrome.runtime.lastError || !results || !results[0].result) {
            status.textContent = "Content script not loaded. Please refresh the page and try again.";
            return;
          }
          chrome.tabs.sendMessage(
            tabs[0].id!,
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
              }
            }
          );
        }
      );
    });
  }

  copyBtn.onclick = async () => {
    try {
      await navigator.clipboard.writeText(markdownEditor.value);
      status.textContent = "Copied to clipboard!";
      setTimeout(() => status.textContent = '', 1200);
    } catch (e) {
      status.textContent = "Failed to copy to clipboard.";
    }
  };
});

function generateMarkdown(jobData: Record<string, any>): string {
  let md = '';
  if (jobData.title) md += `# ${jobData.title}\n`;
  if (jobData.body) md += `\n${jobData.body}\n`;
  if (jobData.metaKeywords && Array.isArray(jobData.metaKeywords) && jobData.metaKeywords.length > 0) {
    md += `\n## Tags\n`;
    md += jobData.metaKeywords.map((kw: string) => `**${kw}**`).join(' ');
    md += '\n';
  }
  if (jobData.headings && Array.isArray(jobData.headings) && jobData.headings.length > 0) {
    md += `\n## Headings\n`;
    for (const h of jobData.headings) {
      md += `- ${h.text} (${h.tag})\n`;
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
      md += `\n## ${key.charAt(0).toUpperCase() + key.slice(1)}\n${value}\n`;
    } else if (Array.isArray(value) && value.length > 0) {
      md += `\n## ${key.charAt(0).toUpperCase() + key.slice(1)}\n`;
      md += value.map(v => `- ${typeof v === 'string' ? v : JSON.stringify(v)}`).join('\n');
      md += '\n';
    }
  }
  if (jobData.url) md += `\n[Source](${jobData.url})\n`;
  return md;
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

