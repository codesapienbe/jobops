// src/popup.ts

// Declare for esbuild global define
// eslint-disable-next-line no-var, @typescript-eslint/no-unused-vars
// @ts-ignore
declare const JOBOPS_BACKEND_URL: string | undefined;

// LLM Configuration
const GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions';
const GROQ_MODEL = 'qwen2.5-32b-instant'; // Free tier model with high usage limits
const OLLAMA_URL = 'http://localhost:11434';
const OLLAMA_MODEL = 'qwen3:1.7b';

document.addEventListener("DOMContentLoaded", async () => {
  let jobData: Record<string, any> = {};
  let resumeContent: string = '';
  const markdownEditor = document.getElementById("markdown-editor") as HTMLTextAreaElement;
  const copyBtn = document.getElementById("copy-markdown") as HTMLButtonElement;
  const generateReportBtn = document.getElementById("generate-report") as HTMLButtonElement;
  const settingsBtn = document.getElementById("settings") as HTMLButtonElement;
  const status = document.getElementById("clip-status") as HTMLElement;
  const resumeUpload = document.getElementById("resume-upload") as HTMLInputElement;
  // Property fields
  const propTitle = document.getElementById("prop-title") as HTMLInputElement;
  const propUrl = document.getElementById("prop-url") as HTMLInputElement;
  const propAuthor = document.getElementById("prop-author") as HTMLInputElement;
  const propPublished = document.getElementById("prop-published") as HTMLInputElement;
  const propCreated = document.getElementById("prop-created") as HTMLInputElement;
  const propDescription = document.getElementById("prop-description") as HTMLInputElement;
  const propTags = document.getElementById("prop-tags") as HTMLInputElement;
  const propHeadings = document.getElementById("prop-headings") as HTMLDivElement;
  const propImages = document.getElementById("prop-images") as HTMLDivElement;
  const propLocation = document.getElementById("prop-location") as HTMLInputElement;
  
  // Enable copy button by default - it should always be clickable
  copyBtn.disabled = false;
  generateReportBtn.disabled = false;

  // Set up toggle functionality
  setupToggleHandlers();

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
      // Copy button is always enabled
      copyBtn.disabled = false;
      generateReportBtn.disabled = false;
    }
  });

  // Set up resume upload handler
  resumeUpload.addEventListener('change', handleResumeUpload);

  // Set up generate report button handler
  generateReportBtn.addEventListener('click', handleGenerateReport);

  // Set up settings button handler
  settingsBtn.addEventListener('click', handleSettings);

  function setupToggleHandlers() {
    // Add click event listeners to all toggle headers
    const toggleHeaders = document.querySelectorAll('.properties-header, .markdown-header');
    toggleHeaders.forEach(header => {
      header.addEventListener('click', () => {
        const toggleTarget = header.getAttribute('data-toggle');
        if (toggleTarget) {
          toggleSection(toggleTarget);
        }
      });
    });
  }

  function toggleSection(sectionId: string) {
    const content = document.getElementById(sectionId);
    const header = content?.parentElement?.querySelector('.properties-header, .markdown-header');
    const toggleIcon = header?.querySelector('.toggle-icon');
    
    if (content && header && toggleIcon) {
      const isCollapsed = content.classList.contains('collapsed');
      
      if (isCollapsed) {
        content.classList.remove('collapsed');
        content.classList.add('expanded');
        toggleIcon.textContent = '▼';
      } else {
        content.classList.remove('expanded');
        content.classList.add('collapsed');
        toggleIcon.textContent = '▶';
      }
    }
  }

  function populatePropertyFields(data: Record<string, any>) {
    propTitle.value = data.title || '';
    propUrl.value = data.url || '';
    propAuthor.value = data.author || '';
    propPublished.value = data.published || '';
    propCreated.value = data.created_at || '';
    propDescription.value = data.description || '';
    propTags.value = Array.isArray(data.metaKeywords) ? data.metaKeywords.join(', ') : (data.metaKeywords || '');
    propLocation.value = data.location || '';
    // Headings as tags
    propHeadings.innerHTML = '';
    if (Array.isArray(data.headings) && data.headings.length > 0) {
      for (const h of data.headings) {
        const tag = document.createElement('span');
        tag.className = 'property-tag';
        tag.textContent = h.text + (h.tag ? ` (${h.tag})` : '');
        propHeadings.appendChild(tag);
      }
    }
    // Images as thumbnails
    propImages.innerHTML = '';
    if (Array.isArray(data.images) && data.images.length > 0) {
      for (const img of data.images) {
        const thumb = document.createElement('img');
        thumb.className = 'property-image-thumb';
        thumb.src = img.src;
        thumb.alt = img.alt || '';
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
    jobData.metaKeywords = propTags.value.split(',').map(t => t.trim()).filter(Boolean);
    jobData.location = propLocation.value;
    markdownEditor.value = generateMarkdown(jobData);
  }

  [propTitle, propUrl, propAuthor, propPublished, propCreated, propDescription, propTags, propLocation].forEach(input => {
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
                // Copy button is always enabled
                copyBtn.disabled = false;
              }
            }
          );
        }
      );
    });
  }

  // Enhanced copy function with notification
  copyBtn.onclick = async () => {
    try {
      const contentToCopy = markdownEditor.value || generateMarkdown(jobData);
      
      if (!contentToCopy.trim()) {
        showNotification("No content to copy!", true);
        return;
      }

      await navigator.clipboard.writeText(contentToCopy);
      
      // Show success notification
      showNotification("✅ Content copied to clipboard!");
      
      // Also update status for additional feedback
      status.textContent = "Copied to clipboard!";
      setTimeout(() => status.textContent = '', 2000);
      
    } catch (e) {
      console.error("Copy failed:", e);
      showNotification("❌ Failed to copy to clipboard", true);
      status.textContent = "Failed to copy to clipboard.";
    }
  };

  // Notification function using Chrome notifications
  function showNotification(message: string, isError: boolean = false) {
    // Try to use Chrome notifications first
    if (chrome.notifications) {
      chrome.notifications.create({
        type: "basic",
        iconUrl: "icon.png",
        title: "JobOps Clipper",
        message: message,
        priority: isError ? 2 : 1
      });
    } else {
      // Fallback to status message
      status.textContent = message;
      setTimeout(() => status.textContent = '', 3000);
    }
  }



  // Handle resume upload
  async function handleResumeUpload(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    
    if (!file) {
      showNotification("No file selected", true);
      return;
    }

    if (file.type !== 'application/pdf') {
      showNotification("Please select a PDF file", true);
      return;
    }

    try {
      status.textContent = "Extracting resume content...";
      resumeContent = await extractPdfContent(file);
      showNotification("✅ Resume content extracted successfully!");
      status.textContent = "Resume ready for report generation";
    } catch (error) {
      console.error("PDF extraction failed:", error);
      showNotification("❌ Failed to extract PDF content", true);
      status.textContent = "PDF extraction failed";
    }
  }

  // Handle generate report
  async function handleGenerateReport() {
    if (!resumeContent) {
      // Trigger file upload if no resume content
      resumeUpload.click();
      return;
    }

    generateReportBtn.disabled = true;
    status.textContent = "Generating comprehensive report...";

    try {
      const report = await generateJobReport(jobData, resumeContent);
      markdownEditor.value = report;
      showNotification("✅ Report generated successfully!");
      status.textContent = "Report generated and ready to copy";
    } catch (error) {
      console.error("Report generation failed:", error);
      const errorMessage = error instanceof Error ? error.message : String(error);
      if (errorMessage.includes('API key')) {
        showNotification("❌ Groq API key not configured. Please set it in extension settings.", true);
        status.textContent = "API key required - check extension settings";
      } else {
        showNotification("❌ Report generation failed", true);
        status.textContent = "Report generation failed";
      }
    } finally {
      generateReportBtn.disabled = false;
      setTimeout(() => status.textContent = '', 3000);
    }
  }

  // Handle settings
  async function handleSettings() {
    const apiKey = await getGroqApiKey();
    const newApiKey = prompt('Enter your Groq API key (leave empty to remove):', apiKey || '');
    
    if (newApiKey !== null) {
      if (newApiKey.trim()) {
        await new Promise<void>((resolve) => {
          chrome.storage.sync.set({ groq_api_key: newApiKey.trim() }, () => {
            showNotification("✅ Groq API key saved!");
            resolve();
          });
        });
      } else {
        await new Promise<void>((resolve) => {
          chrome.storage.sync.remove(['groq_api_key'], () => {
            showNotification("✅ Groq API key removed!");
            resolve();
          });
        });
      }
    }
  }
});

function generateMarkdown(jobData: Record<string, any>): string {
  let md = '';
  if (jobData.title) md += `# ${jobData.title}\n`;
  if (jobData.body) md += `\n${jobData.body}\n`;
  if (jobData.location) md += `\n**Location:** ${jobData.location}\n`;
  if (jobData.metaKeywords && Array.isArray(jobData.metaKeywords) && jobData.metaKeywords.length > 0) {
    md += `\n## Tags\n`;
    md += jobData.metaKeywords.map((kw: string) => `**${kw}**`).join(' ');
    md += '\n';
  }
  // Remove headings and images from markdown
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

// Extract PDF content using PDF.js
async function extractPdfContent(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = async function(e) {
      try {
        const typedarray = new Uint8Array(e.target?.result as ArrayBuffer);
        
        // Use PDF.js to extract text
        const pdfjsLib = (window as any)['pdfjs-dist/build/pdf'];
        if (!pdfjsLib) {
          // Fallback: try to load PDF.js dynamically
          const script = document.createElement('script');
          script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
          script.onload = () => extractPdfWithLibrary(typedarray, resolve, reject);
          script.onerror = () => reject(new Error('Failed to load PDF.js'));
          document.head.appendChild(script);
        } else {
          extractPdfWithLibrary(typedarray, resolve, reject);
        }
      } catch (error) {
        reject(error);
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsArrayBuffer(file);
  });
}

async function extractPdfWithLibrary(typedarray: Uint8Array, resolve: (text: string) => void, reject: (error: Error) => void) {
  try {
    const pdfjsLib = (window as any)['pdfjs-dist/build/pdf'];
    const loadingTask = pdfjsLib.getDocument({ data: typedarray });
    const pdf = await loadingTask.promise;
    
    let fullText = '';
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const textContent = await page.getTextContent();
      const pageText = textContent.items.map((item: any) => item.str).join(' ');
      fullText += pageText + '\n';
    }
    
    resolve(fullText.trim());
  } catch (error) {
    reject(new Error(`PDF extraction failed: ${error}`));
  }
}

// Generate comprehensive job report using LLM
async function generateJobReport(jobData: Record<string, any>, resumeContent: string): Promise<string> {
  const prompt = `You are an expert job application analyst. Based on the provided job posting data and resume content, generate a comprehensive job application tracking report.

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
    // Try Groq first
    const groqResponse = await callGroqAPI(prompt);
    if (groqResponse) {
      return groqResponse;
    }
  } catch (error) {
    console.warn('Groq API failed, falling back to Ollama:', error);
  }

  // Fallback to Ollama
  try {
    const ollamaResponse = await callOllamaAPI(prompt);
    if (ollamaResponse) {
      return ollamaResponse;
    }
  } catch (error) {
    console.error('Ollama API also failed:', error);
  }

  throw new Error('Both Groq and Ollama APIs failed');
}

// Call Groq API
async function callGroqAPI(prompt: string): Promise<string | null> {
  try {
    // Get API key from storage or environment
    const apiKey = await getGroqApiKey();
    if (!apiKey) {
      console.warn('No Groq API key found');
      throw new Error('Groq API key not configured');
    }

    const response = await fetch(GROQ_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: GROQ_MODEL,
        messages: [
          {
            role: 'system',
            content: 'You are an expert job application analyst and career advisor. Provide comprehensive, actionable insights and fill out templates completely.'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.3,
        max_tokens: 4000,
        stream: false
      })
    });

    if (!response.ok) {
      throw new Error(`Groq API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data.choices?.[0]?.message?.content || null;
  } catch (error) {
    console.error('Groq API call failed:', error);
    return null;
  }
}

// Call Ollama API (fallback)
async function callOllamaAPI(prompt: string): Promise<string | null> {
  try {
    const response = await fetch(`${OLLAMA_URL}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: OLLAMA_MODEL,
        prompt: prompt,
        stream: false
      })
    });

    if (!response.ok) {
      throw new Error(`Ollama API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data.response || null;
  } catch (error) {
    console.error('Ollama API call failed:', error);
    return null;
  }
}

// Get Groq API key from Chrome storage
async function getGroqApiKey(): Promise<string | null> {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['groq_api_key'], (result) => {
      resolve(result.groq_api_key || null);
    });
  });
}



