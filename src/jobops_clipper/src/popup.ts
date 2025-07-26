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

// Global console logging functions
let consoleOutput: HTMLElement | null = null;

function logToConsole(message: string, level: 'info' | 'success' | 'warning' | 'error' | 'debug' | 'progress' = 'info') {
  if (!consoleOutput) return;
  
  const timestamp = new Date().toLocaleTimeString();
  const line = document.createElement('div');
  line.className = `console-line ${level}`;
  line.innerHTML = `<span style="color: #888;">[${timestamp}]</span> ${message}`;
  
  consoleOutput.appendChild(line);
  consoleOutput.scrollTop = consoleOutput.scrollHeight;
  
  // Also log to browser console for debugging
  console.log(`[${level.toUpperCase()}] ${message}`);
}

function clearConsole() {
  if (consoleOutput) {
    consoleOutput.innerHTML = '';
    logToConsole("🧹 Console cleared", "info");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  let jobData: Record<string, any> = {};
  let resumeContent: string = '';
  const markdownEditor = document.getElementById("markdown-editor") as HTMLTextAreaElement;
  const copyBtn = document.getElementById("copy-markdown") as HTMLButtonElement;
  const generateReportBtn = document.getElementById("generate-report") as HTMLButtonElement;
  const settingsBtn = document.getElementById("settings") as HTMLButtonElement;
  const status = document.getElementById("clip-status") as HTMLElement;
  if (!status) {
    console.error("Status element not found!");
  }
  const resumeUpload = document.getElementById("resume-upload") as HTMLInputElement;
  
  // Console monitor elements
  consoleOutput = document.getElementById("console-output") as HTMLElement;
  const clearConsoleBtn = document.getElementById("clear-console") as HTMLButtonElement;
  
  // Validate console elements
  if (!consoleOutput) {
    console.error("Console output element not found!");
  } else {
    logToConsole("🔍 Console monitor initialized", "info");
  }
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
      logToConsole("📨 Received preview data from content script", "info");
      logToConsole(`📊 Job title: ${msg.jobData.title || 'N/A'}`, "info");
      jobData = msg.jobData;
      populatePropertyFields(jobData);
      markdownEditor.value = generateMarkdown(jobData);
      // Copy button is always enabled
      copyBtn.disabled = false;
      generateReportBtn.disabled = false;
      logToConsole("✅ Preview data processed successfully", "success");
    }
  });

  // Set up resume upload handler
  if (resumeUpload) {
    console.log("Resume upload element found, adding event listener");
    resumeUpload.addEventListener('change', handleResumeUpload);
  } else {
    console.error("Resume upload element not found!");
  }

  // Set up generate report button handler
  generateReportBtn.addEventListener('click', handleGenerateReport);

  // Set up settings button handler
  settingsBtn.addEventListener('click', handleSettings);

  // Set up console clear button handler
  if (clearConsoleBtn) {
    clearConsoleBtn.addEventListener('click', clearConsole);
  }

  // Initialize console
  logToConsole("🚀 JobOps Clipper initialized", "info");
  logToConsole("📋 Ready to process job postings and resumes", "success");

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
    logToConsole("🌐 Requesting job data from current page...", "info");
    
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]?.id) {
        logToConsole("❌ No active tab found", "error");
        return;
      }
      
      logToConsole("🔍 Checking content script availability...", "debug");
      chrome.scripting.executeScript(
        {
          target: { tabId: tabs[0].id },
          func: () => !!window && !!window.document && !!window.document.body,
        },
        (results) => {
          if (chrome.runtime.lastError || !results || !results[0].result) {
            logToConsole("❌ Content script not loaded. Please refresh the page and try again.", "error");
            status.textContent = "Content script not loaded. Please refresh the page and try again.";
            return;
          }
          
          logToConsole("✅ Content script available, requesting page data...", "success");
          chrome.tabs.sendMessage(
            tabs[0].id!,
            { action: "clip_page" },
            (response) => {
              if (chrome.runtime.lastError) {
                logToConsole("❌ Could not connect to content script. Try refreshing the page.", "error");
                status.textContent = "Could not connect to content script. Try refreshing the page.";
                return;
              }
              if (response && response.jobData) {
                logToConsole("✅ Job data received successfully!", "success");
                logToConsole(`📊 Job title: ${response.jobData.title || 'N/A'}`, "info");
                jobData = response.jobData;
                populatePropertyFields(jobData);
                markdownEditor.value = generateMarkdown(jobData);
                // Copy button is always enabled
                copyBtn.disabled = false;
              } else {
                logToConsole("⚠️ No job data received from content script", "warning");
              }
            }
          );
        }
      );
    });
  }

  // Enhanced copy function with notification
  copyBtn.onclick = async () => {
    logToConsole("📋 Copy to clipboard triggered", "info");
    
    try {
      const contentToCopy = markdownEditor.value || generateMarkdown(jobData);
      
      if (!contentToCopy.trim()) {
        logToConsole("❌ No content to copy", "error");
        showNotification("No content to copy!", true);
        return;
      }

      logToConsole(`📋 Copying content (${contentToCopy.length} characters) to clipboard...`, "progress");
      await navigator.clipboard.writeText(contentToCopy);
      
      // Show success notification
      logToConsole("✅ Content copied to clipboard successfully!", "success");
      showNotification("✅ Content copied to clipboard!");
      
      // Also update status for additional feedback
      status.textContent = "Copied to clipboard!";
      setTimeout(() => status.textContent = '', 2000);
      
    } catch (e) {
      logToConsole(`❌ Copy failed: ${e}`, "error");
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
    logToConsole("📁 Resume upload triggered", "info");
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    
    if (!file) {
      logToConsole("❌ No file selected", "error");
      showNotification("No file selected", true);
      return;
    }

    if (file.type !== 'application/pdf') {
      logToConsole("❌ Invalid file type - PDF required", "error");
      showNotification("Please select a PDF file", true);
      return;
    }

    logToConsole(`📄 Starting PDF extraction: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, "progress");

    try {
      // Step 1: Start extraction
      status.textContent = "📄 Loading PDF file...";
      status.className = "loading";
      showNotification("📄 Loading PDF file...");
      logToConsole("📄 Loading PDF file into memory...", "progress");

      // Step 2: Extract content
      status.textContent = "🔍 Extracting text content from PDF...";
      status.className = "loading";
      showNotification("🔍 Extracting PDF content...");
      logToConsole("🔍 Extracting text content from PDF...", "progress");
      
      resumeContent = await extractPdfContent(file);
      
      logToConsole(`✅ PDF extraction completed! Content length: ${resumeContent.length} characters`, "success");
      
      // Step 3: Success
      status.textContent = "✅ Resume content extracted successfully!";
      status.className = "success";
      showNotification("✅ Resume content extracted successfully!");
      
      // Step 4: Ready for generation
      setTimeout(() => {
        status.textContent = "📋 Resume ready - click 📊 Generate Report to continue";
        status.className = "success";
        logToConsole("📋 Resume ready for report generation", "success");
      }, 2000);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logToConsole(`❌ PDF extraction failed: ${errorMessage}`, "error");
      status.textContent = `❌ PDF extraction failed: ${errorMessage}`;
      status.className = "error";
      showNotification(`❌ Failed to extract PDF content: ${errorMessage}`, true);
    }
  }

  // Handle generate report
  async function handleGenerateReport() {
    if (!resumeContent) {
      logToConsole("📁 No resume content found, triggering file upload", "warning");
      // Trigger file upload if no resume content
      resumeUpload.click();
      return;
    }

    logToConsole("🚀 Starting report generation process", "info");
    generateReportBtn.disabled = true;
    status.textContent = "🔄 Starting report generation...";
    status.className = "loading";
    showNotification("🔄 Starting report generation...");

    try {
      // Step 1: Check API key
      logToConsole("🔑 Checking API configuration...", "progress");
      status.textContent = "🔑 Checking API configuration...";
      status.className = "loading";
      const apiKey = await getGroqApiKey();
      if (!apiKey) {
        throw new Error('Groq API key not configured');
      }
      logToConsole("✅ API key found, proceeding with report generation", "success");
      showNotification("✅ API key found, proceeding...");

      // Step 2: Prepare data
      logToConsole("📊 Preparing job data and resume content...", "progress");
      status.textContent = "📊 Preparing job data and resume content...";
      status.className = "loading";
      showNotification("📊 Preparing data for analysis...");

      // Step 3: Generate report with progress updates
      logToConsole("🤖 Sending data to Groq API for analysis...", "progress");
      status.textContent = "🤖 Sending data to Groq API for analysis...";
      status.className = "loading";
      showNotification("🤖 Analyzing with Groq API...");
      
      const report = await generateJobReport(jobData, resumeContent);
      
      // Step 4: Success
      logToConsole("✅ Report generated successfully!", "success");
      status.textContent = "✅ Report generated successfully!";
      status.className = "success";
      showNotification("✅ Report generated successfully!");
      markdownEditor.value = report;
      
      // Keep success message visible longer
      setTimeout(() => {
        status.textContent = "📋 Report ready - use Copy button to copy content";
        status.className = "success";
        logToConsole("📋 Report ready for copying", "success");
      }, 2000);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logToConsole(`❌ Report generation failed: ${errorMessage}`, "error");
      
      if (errorMessage.includes('API key')) {
        logToConsole("🔧 API key required - please configure in settings", "warning");
        status.textContent = "❌ API key required - click ⚙️ to configure";
        status.className = "error";
        showNotification("❌ Groq API key not configured. Click ⚙️ to set it up.", true);
      } else if (errorMessage.includes('Groq API')) {
        logToConsole("⚠️ Groq API failed, trying Ollama fallback...", "warning");
        status.textContent = "⚠️ Groq API failed, trying Ollama fallback...";
        status.className = "loading";
        showNotification("⚠️ Groq API failed, trying Ollama...");
        
        try {
          logToConsole("🔄 Attempting Ollama fallback...", "progress");
          status.textContent = "🔄 Attempting Ollama fallback...";
          status.className = "loading";
          const report = await generateJobReportWithOllama(jobData, resumeContent);
          markdownEditor.value = report;
          logToConsole("✅ Report generated with Ollama fallback!", "success");
          status.textContent = "✅ Report generated with Ollama!";
          status.className = "success";
          showNotification("✅ Report generated with Ollama fallback!");
        } catch (ollamaError) {
          logToConsole("❌ Both Groq and Ollama failed", "error");
          status.textContent = "❌ Both Groq and Ollama failed";
          status.className = "error";
          showNotification("❌ Report generation failed on all services", true);
        }
      } else {
        logToConsole("❌ Report generation failed with unknown error", "error");
        status.textContent = "❌ Report generation failed";
        status.className = "error";
        showNotification("❌ Report generation failed", true);
      }
    } finally {
      generateReportBtn.disabled = false;
    }
  }

  // Handle settings
  async function handleSettings() {
    logToConsole("⚙️ Settings dialog opened", "info");
    const apiKey = await getGroqApiKey();
    const newApiKey = prompt('Enter your Groq API key (leave empty to remove):', apiKey || '');
    
    if (newApiKey !== null) {
      if (newApiKey.trim()) {
        logToConsole("🔑 Saving new Groq API key...", "progress");
        await new Promise<void>((resolve) => {
          chrome.storage.sync.set({ groq_api_key: newApiKey.trim() }, () => {
            logToConsole("✅ Groq API key saved successfully!", "success");
            showNotification("✅ Groq API key saved!");
            resolve();
          });
        });
      } else {
        logToConsole("🗑️ Removing Groq API key...", "warning");
        await new Promise<void>((resolve) => {
          chrome.storage.sync.remove(['groq_api_key'], () => {
            logToConsole("✅ Groq API key removed successfully!", "success");
            showNotification("✅ Groq API key removed!");
            resolve();
          });
        });
      }
    } else {
      logToConsole("❌ Settings dialog cancelled", "info");
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
    logToConsole("🔄 Starting PDF content extraction...", "progress");
    
    const reader = new FileReader();
    reader.onload = async function(e) {
      try {
        logToConsole("📖 File read successfully, creating typed array...", "debug");
        const typedarray = new Uint8Array(e.target?.result as ArrayBuffer);
        logToConsole(`📊 Typed array created, size: ${typedarray.length} bytes`, "debug");
        
        // Use PDF.js to extract text
        const pdfjsLib = (window as any)['pdfjs-dist/build/pdf'];
        logToConsole(`📚 PDF.js library available: ${!!pdfjsLib}`, "debug");
        
        if (!pdfjsLib) {
          // Fallback: try to load PDF.js dynamically
          logToConsole("📚 PDF.js not available, loading dynamically...", "progress");
          const status = document.getElementById("clip-status") as HTMLElement;
          if (status) {
            status.textContent = "📚 Loading PDF processing library...";
            status.className = "loading";
          }
          
          const script = document.createElement('script');
          script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
          script.onload = () => {
            logToConsole("✅ PDF.js loaded dynamically, proceeding with extraction...", "success");
            extractPdfWithLibrary(typedarray, resolve, reject);
          };
          script.onerror = () => {
            logToConsole("❌ Failed to load PDF.js from CDN", "error");
            reject(new Error('Failed to load PDF.js'));
          };
          document.head.appendChild(script);
        } else {
          logToConsole("✅ PDF.js already available, proceeding with extraction...", "success");
          extractPdfWithLibrary(typedarray, resolve, reject);
        }
      } catch (error) {
        logToConsole(`❌ Error in PDF extraction: ${error}`, "error");
        reject(error);
      }
    };
    reader.onerror = (error) => {
      logToConsole(`❌ FileReader error: ${error}`, "error");
      reject(new Error('Failed to read file'));
    };
    reader.readAsArrayBuffer(file);
  });
}

async function extractPdfWithLibrary(typedarray: Uint8Array, resolve: (text: string) => void, reject: (error: Error) => void) {
  try {
    logToConsole("🔄 Starting PDF library extraction...", "progress");
    const pdfjsLib = (window as any)['pdfjs-dist/build/pdf'];
    
    if (!pdfjsLib) {
      throw new Error('PDF.js library not available');
    }
    
    // Show loading PDF document
    const status = document.getElementById("clip-status") as HTMLElement;
    if (status) {
      status.textContent = "📖 Loading PDF document...";
      status.className = "loading";
    }
    
    logToConsole("📖 Creating PDF document from typed array...", "progress");
    const loadingTask = pdfjsLib.getDocument({ data: typedarray });
    const pdf = await loadingTask.promise;
    
    logToConsole(`📄 PDF document loaded, pages: ${pdf.numPages}`, "success");
    let fullText = '';
    const totalPages = pdf.numPages;
    
    for (let i = 1; i <= totalPages; i++) {
      logToConsole(`📄 Processing page ${i} of ${totalPages}...`, "progress");
      
      // Update progress for each page
      const status = document.getElementById("clip-status") as HTMLElement;
      if (status) {
        status.textContent = `📄 Processing page ${i} of ${totalPages}...`;
        status.className = "loading";
      }
      
      const page = await pdf.getPage(i);
      const textContent = await page.getTextContent();
      const pageText = textContent.items.map((item: any) => item.str).join(' ');
      fullText += pageText + '\n';
      
      logToConsole(`✅ Page ${i} processed, text length: ${pageText.length} characters`, "debug");
    }
    
    logToConsole(`🎉 PDF extraction completed! Total text length: ${fullText.length} characters`, "success");
    resolve(fullText.trim());
  } catch (error) {
    logToConsole(`❌ Error in PDF library extraction: ${error}`, "error");
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
    throw new Error('Groq API failed');
  }

  throw new Error('Both Groq and Ollama APIs failed');
}

// Generate report using only Ollama (for fallback)
async function generateJobReportWithOllama(jobData: Record<string, any>, resumeContent: string): Promise<string> {
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

  const ollamaResponse = await callOllamaAPI(prompt);
  if (ollamaResponse) {
    return ollamaResponse;
  }

  throw new Error('Ollama API failed');
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



