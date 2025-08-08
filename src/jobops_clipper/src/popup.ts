// src/popup.ts

// Declare for esbuild global define
// eslint-disable-next-line no-var, @typescript-eslint/no-unused-vars
// @ts-ignore
declare const JOBOPS_BACKEND_URL: string | undefined;

// Import database and data manager
import { jobOpsDataManager } from './repository';
import { jobOpsDatabase } from './database';

// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import createDOMPurify from 'dompurify';
const DOMPurify = (createDOMPurify as any)(window as unknown as Window);

// Import i18n manager
import { i18n, SupportedLanguage } from './i18n';
import { LinearIntegrationService } from './integration';

// LLM Configuration
const GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions';
const GROQ_MODEL = 'llama-3.1-8b-instant'; // Free tier model with high usage limits
const OLLAMA_URL = 'http://localhost:11434';
const OLLAMA_MODEL = 'qwen3:1.7b';

// Global console logging functions
let consoleOutput: HTMLElement | null = null;

// Global variables for streaming
let isGenerating = false;
let abortController: AbortController | null = null;

// Theme management
type ThemeMode = 'light' | 'dark' | 'system';
let currentTheme: ThemeMode = 'system';
let isDarkMode = false;

// Theme management functions
function detectSystemTheme(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

function updateThemeIcon(): void {
  const themeToggle = document.getElementById('theme-toggle') as HTMLButtonElement;
  if (themeToggle) {
    const isDark = currentTheme === 'dark' || (currentTheme === 'system' && isDarkMode);
    themeToggle.textContent = isDark ? '☀️' : '🌙';
    themeToggle.setAttribute('aria-label', isDark ? 'Switch to Light Theme' : 'Switch to Dark Theme');
  }
}

function applyTheme(theme: ThemeMode): void {
  const html = document.documentElement;
  const isDark = theme === 'dark' || (theme === 'system' && detectSystemTheme());
  
  if (isDark) {
    html.classList.remove('theme-light');
    isDarkMode = true;
  } else {
    html.classList.add('theme-light');
    isDarkMode = false;
  }
  
  currentTheme = theme;
  updateThemeIcon();
  
  // Log theme change
  logToConsole(`${i18n.getConsoleMessage('themeSwitched')} ${theme} ${i18n.getConsoleMessage('mode')}`, 'info');
}

function initializeTheme(): void {
  // Always use system theme
  applyTheme('system');
  
  // Listen for system theme changes
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  mediaQuery.addEventListener('change', (e) => {
    applyTheme('system');
  });
}




function initializeLanguage(): void {
  // Initialize i18n manager with browser locale only
  i18n.initialize().then(() => {
    // Update UI with current language (browser locale)
    i18n.updateUI();
    
    logToConsole(`🌐 Language system initialized: ${i18n.getCurrentLanguage()}`, 'info');
  }).catch(error => {
    logToConsole(`❌ Error initializing language system: ${error}`, 'error');
  });
}



function sanitizeLogMessage(message: string): string {
  try {
    let sanitized = message;
    sanitized = sanitized.replace(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, '[redacted-email]');
    sanitized = sanitized.replace(/\b(\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b/g, '[redacted-phone]');
    return sanitized;
  } catch {
    return message;
  }
}

let logQueue: Array<{ html: string; level: 'info' | 'success' | 'warning' | 'error' | 'debug' | 'progress' }> = [];
let logFlushTimer: number | null = null;
function logToConsole(message: string, level: 'info' | 'success' | 'warning' | 'error' | 'debug' | 'progress' = 'info') {
  if (!consoleOutput) return;
  const safe = escapeHtml(sanitizeLogMessage(message));
  const timestamp = new Date().toLocaleTimeString();
  const html = `<span style="color: #888;">[${timestamp}]</span> ${safe}`;
  logQueue.push({ html, level });
  if (logFlushTimer === null) {
    logFlushTimer = window.setTimeout(() => {
      if (!consoleOutput) { logQueue = []; logFlushTimer = null; return; }
      const fragment = document.createDocumentFragment();
      for (const entry of logQueue) {
        const line = document.createElement('div');
        line.className = `console-line ${entry.level}`;
        line.innerHTML = entry.html;
        fragment.appendChild(line);
      }
      consoleOutput.appendChild(fragment);
      consoleOutput.scrollTop = consoleOutput.scrollHeight;
      logQueue = [];
      logFlushTimer = null;
    }, 50);
  }
  console.log(`[${level.toUpperCase()}] ${message}`);
}

function clearConsole() {
  if (consoleOutput) {
    consoleOutput.innerHTML = '';
    logToConsole(i18n.getConsoleMessage('consoleCleared'), "info");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  let jobData: Record<string, any> = {};
  let resumeContent: string = '';
  const markdownEditor = document.getElementById("markdown-editor") as HTMLTextAreaElement;
  const copyBtn = document.getElementById("copy-markdown") as HTMLButtonElement;
  const generateReportBtn = document.getElementById("generate-report") as HTMLButtonElement;
  const settingsBtn = document.getElementById("settings") as HTMLButtonElement;
  
  // Real-time response elements
  const realtimeResponse = document.getElementById("realtime-response") as HTMLDivElement;
  const stopGenerationBtn = document.getElementById("stop-generation") as HTMLButtonElement;
  const copyRealtimeBtn = document.getElementById("copy-realtime") as HTMLButtonElement;
  const resumeUpload = document.getElementById("resume-upload") as HTMLInputElement;
  
  // Console monitor elements
  consoleOutput = document.getElementById("console-output") as HTMLElement;
  const clearConsoleBtn = document.getElementById("clear-console") as HTMLButtonElement;
  
  // Validate console elements
  if (!consoleOutput) {
    console.error("Console output element not found!");
  } else {
    logToConsole(i18n.getConsoleMessage('initialized'), "info");
  }
  
  // Initialize theme system (system theme only)
  initializeTheme();
  
  // Initialize language system (browser locale only)
  initializeLanguage();
  
  // Background worker health ping
  try {
    chrome.runtime.sendMessage({ action: 'ping' }, (resp) => {
      if (chrome.runtime.lastError) {
        logToConsole(`⚠️ Background worker unreachable: ${chrome.runtime.lastError.message}`, 'warning');
      } else if (resp === 'pong') {
        logToConsole('✅ Background worker healthy', 'debug');
      } else {
        logToConsole('⚠️ Unexpected background worker response', 'warning');
      }
    });
  } catch (e) {
    logToConsole(`⚠️ Background ping failed: ${e instanceof Error ? e.message : String(e)}`, 'warning');
  }

  
  // Set up button event listeners
  if (copyBtn) {
    copyBtn.addEventListener('click', async (event) => {
      event.preventDefault();
      try {
        await navigator.clipboard.writeText(markdownEditor.value);
        logToConsole(i18n.getConsoleMessage('markdownCopied'), "success");
        showNotification(i18n.getNotificationMessage('copied'));
      } catch (error) {
        logToConsole(`${i18n.getConsoleMessage('markdownCopyFailed')}: ${error}`, "error");
        showNotification(i18n.getNotificationMessage('copyFailed'), true);
      }
    });
  }
  
  if (generateReportBtn) {
    generateReportBtn.addEventListener('click', (event) => {
      event.preventDefault();
      handleGenerateReport();
    });
  }
  
  if (settingsBtn) {
    settingsBtn.addEventListener('click', (event) => {
      event.preventDefault();
      handleSettings();
    });
  }
  
  if (stopGenerationBtn) {
    stopGenerationBtn.addEventListener('click', (event) => {
      event.preventDefault();
      handleStopGeneration();
    });
  }
  
  if (copyRealtimeBtn) {
    copyRealtimeBtn.addEventListener('click', (event) => {
      event.preventDefault();
      handleCopyRealtime();
    });
  }
  
  if (clearConsoleBtn) {
    clearConsoleBtn.addEventListener('click', (event) => {
      event.preventDefault();
      clearConsole();
    });
  }
  
  // Add Linear export button event listener
  const exportLinearBtn = document.getElementById("export-linear");
  if (exportLinearBtn) {
    exportLinearBtn.addEventListener('click', (event) => {
      event.preventDefault();
      handleExportToLinear();
    });
    logToConsole("📤 Linear export button event listener added", "debug");
  }
  
  if (resumeUpload) {
    resumeUpload.addEventListener('change', handleResumeUpload);
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
  
  // Enable buttons by default - they should always be clickable
  copyBtn.disabled = false;
  generateReportBtn.disabled = false;
  
  // Add visual feedback for button readiness
  logToConsole(i18n.getConsoleMessage('generateReportReady'), "success");
  generateReportBtn.style.opacity = "1";
  generateReportBtn.style.cursor = "pointer";

  // Set up toggle functionality
  setupToggleHandlers();

  // Set up auto-save and save-on-collapse functionality
  setupAutoSave();
  setupSaveOnCollapse();

  // Set backendUrl from env or fallback, then store in chrome.storage.sync
  const backendUrl: string = (typeof JOBOPS_BACKEND_URL !== 'undefined' ? JOBOPS_BACKEND_URL : 'http://localhost:8877');
  chrome.storage.sync.set({ jobops_backend_url: backendUrl }, async () => {
    requestJobData();
  });

  // Scan for missing API keys on startup
  await scanForMissingApiKeys();

  // Listen for preview data from content script
  chrome.runtime.onMessage.addListener(async (msg, _sender, _sendResponse) => {
    if (msg.action === "show_preview" && msg.jobData) {
      logToConsole(i18n.getConsoleMessage('previewDataReceived'), "info");
      logToConsole(`${i18n.getConsoleMessage('jobTitle')}: ${msg.jobData.title || 'N/A'}`, "info");
      jobData = msg.jobData;
      
                      // Check if job application already exists
                const jobExists = await jobOpsDataManager.checkAndLoadExistingJob(jobData.url);
                if (jobExists) {
                  logToConsole(i18n.getConsoleMessage('existingJobFound'), "info");
                  showNotification(i18n.getNotificationMessage('existingJobLoaded'));
                } else {
                  // Check if we have sufficient content to create a database record
                  const { hasContent, missingSections, contentQuality } = checkRequiredSectionsContent();
                  
                  if (hasContent) {
                    logToConsole(`${i18n.getConsoleMessage('newJobCreated')} (${i18n.getConsoleMessage('contentQuality')}: ${contentQuality})`, "info");
                    try {
                      await jobOpsDataManager.createNewJobApplication(jobData);
                      showNotification(`${i18n.getNotificationMessage('newJobCreated')} (${contentQuality} content)`);
                      
                      // Provide enhanced guidance for content improvement
                      validateAndProvideFeedback(contentQuality, missingSections);
                    } catch (error) {
                      logToConsole(`${i18n.getConsoleMessage('errorCreatingJob')}: ${error}`, "error");
                      showNotification(i18n.getNotificationMessage('jobCreationError'), true);
                    }
                  } else {
                    const minRequirements = missingSections.map(section => {
                      const req = [
                        { name: 'Position Details', minLength: 50 },
                        { name: 'Job Requirements', minLength: 50 },
                        { name: 'Company Information', minLength: 30 },
                        { name: 'Offer Details', minLength: 20 }
                      ].find(s => s.name === section);
                      return `${section} (${req?.minLength || 50}+ chars)`;
                    }).join(', ');
                    
                    logToConsole(`⚠️ Insufficient content for database creation. Missing: ${missingSections.join(', ')}`, "warning");
                  }
                }
      
      populatePropertyFields(jobData);
      markdownEditor.value = generateMarkdown(jobData);
      // Copy button is always enabled
      copyBtn.disabled = false;
      generateReportBtn.disabled = false;
      logToConsole(i18n.getConsoleMessage('previewDataProcessed'), "success");
    }
  });

  // Set up resume upload handler
  if (resumeUpload) {
    console.log("Resume upload element found, adding event listener");
    resumeUpload.addEventListener('change', handleResumeUpload);
  } else {
    console.error("Resume upload element not found!");
  }

  // Set up generate report button handler with immediate feedback
  generateReportBtn.addEventListener('click', (event) => {
    console.log("🎯 GENERATE REPORT BUTTON CLICKED - DIRECT CONSOLE LOG");
    logToConsole(i18n.getConsoleMessage('generateReportClicked'), "info");
    
    // Immediate visual feedback
    generateReportBtn.style.transform = "scale(0.95)";
    setTimeout(() => {
      generateReportBtn.style.transform = "scale(1)";
    }, 100);
    
    // Call the handler
    handleGenerateReport();
  });

  // Set up settings button handler
  settingsBtn.addEventListener('click', handleSettings);

  // Add test API functionality
  settingsBtn.addEventListener('contextmenu', handleTestAPI);

  // Set up console clear button handler
  if (clearConsoleBtn) {
    clearConsoleBtn.addEventListener('click', clearConsole);
  }

  // Set up real-time response handlers
  if (stopGenerationBtn) {
    stopGenerationBtn.addEventListener('click', handleStopGeneration);
  }
  if (copyRealtimeBtn) {
    copyRealtimeBtn.addEventListener('click', handleCopyRealtime);
  }

  // Listen for job data loaded events from the repository
  window.addEventListener('jobDataLoaded', function(event: Event) {
    const customEvent = event as CustomEvent;
    const loadedData = customEvent.detail;
    logToConsole(i18n.getConsoleMessage('jobDataLoaded'), "info");
    
    // Populate properties with loaded data instead of scraped data
    if (loadedData && loadedData.jobApplication) {
      const jobApp = loadedData.jobApplication;
      populatePropertyFields({
        title: jobApp.job_title || '',
        url: jobApp.canonical_url || '',
        author: '',
        published: jobApp.application_date || '',
        created_at: jobApp.created_at || '',
        description: '',
        metaKeywords: [],
        location: '',
        company: jobApp.company_name || ''
      });
      
      // Also populate job sections if they exist
      if (loadedData.positionDetails && loadedData.positionDetails.length > 0) {
        const posDetails = loadedData.positionDetails[0];
        // Populate position details section
        const jobTitleInput = document.getElementById('job-title') as HTMLInputElement;
        const companyNameInput = document.getElementById('company-name') as HTMLInputElement;
        const locationInput = document.getElementById('location') as HTMLInputElement;
        
        if (jobTitleInput) jobTitleInput.value = posDetails.job_title || '';
        if (companyNameInput) companyNameInput.value = posDetails.company_name || '';
        if (locationInput) locationInput.value = posDetails.location || '';
      }
      
      logToConsole(i18n.getConsoleMessage('propertiesUpdated'), "success");
    }
  });

  // Initialize console
  logToConsole(i18n.getConsoleMessage('jobOpsInitialized'), "info");
  logToConsole(i18n.getConsoleMessage('readyToProcess'), "success");
  
  // Initialize button position for collapsed console
  document.documentElement.style.setProperty('--button-bottom', '48px');
  
  // Initialize form padding for collapsed console
  const form = document.querySelector('#properties-form');
  if (form) {
    (form as HTMLElement).style.paddingBottom = '80px';
  }

  // Log to application.log as required by rules
  const logToApplicationLog = (level: string, message: string, data?: any) => {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      component: 'JobOpsClipper',
      message,
      correlation_id: `jobops_${Date.now()}`,
      user_id: 'extension_user',
      request_id: `req_${Date.now()}`,
      ...(data && { data })
    };
    
    // In a real extension, this would write to a file
    // For now, we'll use console.log for the structured log
    console.log('APPLICATION_LOG:', JSON.stringify(logEntry));
  };

  // Enhanced content validation with better user feedback
  function validateAndProvideFeedback(contentQuality: 'minimal' | 'adequate' | 'complete', missingSections: string[]): void {
    const guidance = getContentGuidance(contentQuality, missingSections);
    
    // Log validation results for monitoring
    logToApplicationLog('INFO', 'Content validation feedback provided', {
      contentQuality,
      missingSections,
      guidanceCount: guidance.length
    });
    
    // Provide user feedback
    guidance.forEach(tip => {
      logToConsole(tip, "info");
    });
    
    // Additional context-specific feedback
    if (contentQuality === 'minimal' && missingSections.length > 0) {
      logToConsole("🔍 Tip: Expand the sections above to add more details", "info");
    } else if (contentQuality === 'adequate') {
      logToConsole("✅ Good progress! Consider adding more specific examples", "success");
    } else if (contentQuality === 'complete') {
      logToConsole("🎉 Excellent! Your application is ready for comprehensive analysis", "success");
    }
  }

  logToApplicationLog('INFO', 'JobOps Clipper extension initialized', {
    version: '1.0.0',
    database_ready: true,
    features: ['job_tracking', 'database_storage', 'ai_analysis']
  });

  logToApplicationLog('INFO', 'Debug console initialized in collapsed state', { initial_state: 'collapsed' });

  // Database utility functions
  async function saveSectionData(sectionName: string, data: any): Promise<void> {
    try {
      const jobInfo = getCurrentJobInfo();
      logToApplicationLog('INFO', `Saving section data`, {
        section: sectionName,
        job_application_id: jobInfo.id,
        canonical_url: jobInfo.url,
        data_keys: Object.keys(data)
      });

      switch (sectionName) {
        case 'position_details':
          await jobOpsDataManager.savePositionDetails(data);
          break;
        case 'job_requirements':
          await jobOpsDataManager.saveJobRequirements(data);
          break;
        case 'company_information':
          await jobOpsDataManager.saveCompanyInformation(data);
          break;
        case 'skills_matrix':
          await jobOpsDataManager.saveSkillsMatrix(data);
          break;
        case 'application_materials':
          await jobOpsDataManager.saveApplicationMaterials(data);
          break;
        case 'interview_schedule':
          await jobOpsDataManager.saveInterviewSchedule(data);
          break;
        case 'interview_preparation':
          await jobOpsDataManager.saveInterviewPreparation(data);
          break;
        case 'communication_log':
          await jobOpsDataManager.saveCommunicationLog(data);
          break;
        case 'key_contacts':
          await jobOpsDataManager.saveKeyContacts(data);
          break;
        case 'interview_feedback':
          await jobOpsDataManager.saveInterviewFeedback(data);
          break;
        case 'offer_details':
          await jobOpsDataManager.saveOfferDetails(data);
          break;
        case 'rejection_analysis':
          await jobOpsDataManager.saveRejectionAnalysis(data);
          break;
        case 'privacy_policy':
          await jobOpsDataManager.savePrivacyPolicy(data);
          break;
        case 'lessons_learned':
          await jobOpsDataManager.saveLessonsLearned(data);
          break;
        case 'performance_metrics':
          await jobOpsDataManager.savePerformanceMetrics(data);
          break;
        case 'advisor_review':
          await jobOpsDataManager.saveAdvisorReview(data);
          break;
        default:
          throw new Error(`Unknown section: ${sectionName}`);
      }
      
      logToApplicationLog('INFO', `Section data saved successfully`, {
        section: sectionName,
        job_application_id: jobInfo.id
      });
      
      logToConsole(`${i18n.getConsoleMessage('sectionSaved')}: ${sectionName}`, "success");
      showNotification(`✅ ${sectionName} saved`);
    } catch (error) {
      const jobInfo = getCurrentJobInfo();
      logToApplicationLog('ERROR', `Failed to save section data`, {
        section: sectionName,
        job_application_id: jobInfo.id,
        error: error instanceof Error ? error.message : String(error)
      });
      
      logToConsole(`${i18n.getConsoleMessage('sectionSaveFailed')} ${sectionName}: ${error}`, "error");
      showNotification(`❌ Error saving ${sectionName}`, true);
      throw error;
    }
  }

  // Check if required sections have sufficient content (255+ chars each)
  function checkRequiredSectionsContent(): { hasContent: boolean; missingSections: string[]; contentQuality: 'minimal' | 'adequate' | 'complete' } {
    const requiredSections = [
      { name: 'Position Details', id: 'position-details', minLength: 50, adequateLength: 150 },
      { name: 'Job Requirements', id: 'job-requirements', minLength: 50, adequateLength: 150 },
      { name: 'Company Information', id: 'company-information', minLength: 30, adequateLength: 100 },
      { name: 'Offer Details', id: 'offer-details', minLength: 20, adequateLength: 80 }
    ];

    const missingSections: string[] = [];
    let hasContent = true;
    let totalContentLength = 0;
    let sectionsWithAdequateContent = 0;

    for (const section of requiredSections) {
      const sectionContent = getSectionContent(section.id);
      const contentLength = sectionContent.trim().length;
      totalContentLength += contentLength;
      
      if (contentLength < section.minLength) {
        missingSections.push(section.name);
        hasContent = false;
      } else if (contentLength >= section.adequateLength) {
        sectionsWithAdequateContent++;
      }
    }

    // Determine content quality based on overall content and section completion
    let contentQuality: 'minimal' | 'adequate' | 'complete' = 'minimal';
    if (totalContentLength >= 500 && sectionsWithAdequateContent >= 2) {
      contentQuality = 'adequate';
    }
    if (totalContentLength >= 800 && sectionsWithAdequateContent >= 3) {
      contentQuality = 'complete';
    }

    // Log content validation results for monitoring
    logToApplicationLog('DEBUG', 'Content validation completed', {
      totalContentLength,
      sectionsWithAdequateContent,
      missingSections,
      contentQuality,
      hasContent
    });

    return { hasContent, missingSections, contentQuality };
  }

  // Get content from a specific section
  function getSectionContent(sectionId: string): string {
    switch (sectionId) {
      case 'position-details':
        return getTextareaValue('position-summary');

      case 'job-requirements':
        return getTextareaValue('requirements-summary');

      case 'company-information':
        return getTextareaValue('company-summary');

      case 'offer-details':
        return getTextareaValue('offer-summary');

      case 'markdown':
        return getTextareaValue('markdown-editor');

      default:
        return '';
    }
  }

  // Provide helpful guidance for content improvement
  function getContentGuidance(contentQuality: 'minimal' | 'adequate' | 'complete', missingSections: string[]): string[] {
    const guidance: string[] = [];
    
    switch (contentQuality) {
      case 'minimal':
        guidance.push("💡 Add more details to improve application quality");
        if (missingSections.includes('Position Details')) {
          guidance.push("📝 Include job title, company, location, salary range, and key responsibilities");
        }
        if (missingSections.includes('Job Requirements')) {
          guidance.push("📋 List required skills, experience level, education, and technical requirements");
        }
        if (missingSections.includes('Company Information')) {
          guidance.push("🏢 Add company size, industry, mission, and recent news");
        }
        break;
        
      case 'adequate':
        guidance.push("✅ Good content level - consider adding more specific details");
        break;
        
      case 'complete':
        guidance.push("🎉 Excellent content level - ready for comprehensive analysis");
        break;
    }
    
    return guidance;
  }

  // Helper functions to get form values
  function getInputValue(id: string): string {
    const element = document.getElementById(id) as HTMLInputElement;
    return element ? element.value : '';
  }

  function getTextareaValue(id: string): string {
    const element = document.getElementById(id) as HTMLTextAreaElement;
    return element ? element.value : '';
  }

  function getSelectValue(id: string): string {
    const element = document.getElementById(id) as HTMLSelectElement;
    return element ? element.value : '';
  }

  function getCheckboxValue(id: string): boolean {
    const element = document.getElementById(id) as HTMLInputElement;
    return element ? element.checked : false;
  }

  function debounce<F extends (...args: any[]) => void>(fn: F, delayMs: number): F {
    let timer: number | undefined;
    return ((...args: any[]) => {
      if (timer) {
        clearTimeout(timer);
      }
      timer = window.setTimeout(() => fn(...args), delayMs);
    }) as F;
  }

  // Collect all form data as JSON
  function collectAllFormData(): any {
    const formData = {
      positionDetails: {
        summary: getTextareaValue('position-summary')
      },
      jobRequirements: {
        summary: getTextareaValue('requirements-summary')
      },
      companyInformation: {
        summary: getTextareaValue('company-summary')
      },
      skillsMatrix: {
        summary: getTextareaValue('skills-assessment')
      },
      applicationMaterials: {
        summary: getTextareaValue('materials-summary')
      },
      interviewSchedule: {
        summary: getTextareaValue('interview-details')
      },
      interviewPreparation: {
        summary: getTextareaValue('preparation-summary')
      },
      communicationLog: {
        summary: getTextareaValue('communication-summary')
      },
      keyContacts: {
        summary: getTextareaValue('contacts-summary')
      },
      interviewFeedback: {
        summary: getTextareaValue('feedback-summary')
      },
      offerDetails: {
        summary: getTextareaValue('offer-summary')
      },
      rejectionAnalysis: {
        summary: getTextareaValue('rejection-summary')
      },
      privacyPolicy: {
        summary: getTextareaValue('privacy-summary')
      },
      lessonsLearned: {
        summary: getTextareaValue('lessons-summary')
      },
      performanceMetrics: {
        summary: getTextareaValue('metrics-summary')
      },
      advisorReview: {
        summary: getTextareaValue('advisor-summary')
      },
      applicationSummary: {
        summary: getTextareaValue('overall-summary')
      },
      markdownPreview: getTextareaValue('markdown-editor'),
      metadata: {
        url: getInputValue('prop-url'),
        title: getInputValue('prop-title'),
        author: getInputValue('prop-author'),
        published: getInputValue('prop-published'),
        created: getInputValue('prop-created'),
        description: getInputValue('prop-description'),
        tags: getInputValue('prop-tags'),
        location: getInputValue('prop-location')
      }
    };

    return formData;
  }

  // Auto-save functionality for form fields
  function setupAutoSave() {
    // Auto-save job data when property fields change
    const autoSaveFields = [propTitle, propUrl, propAuthor, propPublished, propCreated, propDescription, propTags, propLocation];

    const triggerAutoSaveDebounced = debounce(async () => {
      try {
        updateJobDataFromFields();

        // Check if we have sufficient content to create a database record
        const { hasContent, missingSections, contentQuality } = checkRequiredSectionsContent();

        if (hasContent) {
          // Save position details with updated job data
          if (jobData.title || jobData.description || jobData.location) {
            await saveSectionData('position_details', {
              job_title: jobData.title,
              job_description: jobData.description,
              location: jobData.location,
              source_url: jobData.url,
              company_name: jobData.company || '',
              salary_range: '',
              employment_type: '',
              experience_level: '',
              remote_work_policy: ''
            });
          }

          logToConsole(i18n.getConsoleMessage('autoSaved'), 'debug');
        } else {
          logToConsole(`${i18n.getConsoleMessage('insufficientContent')}. Missing: ${missingSections.join(', ')}`, 'debug');
        }
      } catch (error) {
        logToConsole(`❌ Auto-save failed: ${error}`, 'error');
      }
    }, 2000);

    autoSaveFields.forEach(field => {
      field.addEventListener('input', triggerAutoSaveDebounced);
    });
  }

  // Setup save-on-collapse functionality for job sections
  function setupSaveOnCollapse() {
    // All job sections will save when collapsed
    const sections = [
      'position-details',
      'job-requirements', 
      'company-information',
      'skills-matrix',
      'application-materials',
      'interview-schedule',
      'interview-preparation',
      'communication-log',
      'key-contacts',
      'interview-feedback',
      'offer-details',
      'rejection-analysis',
      'privacy-policy',
      'lessons-learned',
      'performance-metrics',
      'advisor-review',
      'application-summary'
    ];

    sections.forEach(sectionName => {
      const sectionElement = document.querySelector(`[data-section="${sectionName}"]`);
      if (sectionElement) {
        const header = sectionElement.querySelector('.job-header');
        const content = sectionElement.querySelector('.job-content');
        
        if (header && content) {
          // Track the previous state to detect collapse
          let wasExpanded = !content.classList.contains('collapsed');
          
          // Override the click handler to add save-on-collapse functionality
          header.addEventListener('click', async (e) => {
            // Check if section was expanded BEFORE the toggle
            const previousState = wasExpanded;
            
            // Update the tracked state after a short delay to let the toggle happen
            setTimeout(() => {
              wasExpanded = !content.classList.contains('collapsed');
              
              // If the section was expanded and is now collapsed, trigger save
              if (previousState && !wasExpanded) {
                handleSectionSave(sectionName);
              }
            }, 50);
          });
        }
      }
    });
  }

  // Handle section save button clicks
  async function handleSectionSave(sectionName: string) {
    try {
      // First check if the specific section has any content at all
      const sectionData = getSectionData(sectionName);
      const hasSectionContent = sectionData && 
        Object.values(sectionData).some(value => 
          typeof value === 'string' && value.trim().length > 0
        );
      
      if (!hasSectionContent) {
        // Section is empty, no need to save or validate
        logToConsole(`${i18n.getConsoleMessage('sectionEmpty')}: ${sectionName}`, "debug");
        return;
      }
      
      logToConsole(`💾 Saving ${sectionName}...`, "info");
      
      // Check if we have sufficient content to save
      const { hasContent, missingSections, contentQuality } = checkRequiredSectionsContent();
      
      if (!hasContent) {
        const minRequirements = missingSections.map(section => {
          const req = [
            { name: 'Position Details', minLength: 50 },
            { name: 'Job Requirements', minLength: 50 },
            { name: 'Company Information', minLength: 30 },
            { name: 'Offer Details', minLength: 20 }
          ].find(s => s.name === section);
          return `${section} (${req?.minLength || 50}+ chars)`;
        }).join(', ');
        
        logToConsole(`${i18n.getConsoleMessage('cannotSave')}. Missing: ${missingSections.join(', ')}`, "warning");
        return;
      }
      
      if (sectionData && Object.keys(sectionData).length > 0) {
        await saveSectionData(sectionName.replace('-', '_'), sectionData);
        logToConsole(`✅ ${sectionName} saved successfully`, "success");
      } else {
        logToConsole(`${i18n.getConsoleMessage('noDataToSave')}: ${sectionName}`, "warning");
      }
    } catch (error) {
      logToConsole(`❌ Failed to save ${sectionName}: ${error}`, "error");
      showNotification(`❌ Failed to save ${sectionName}`, true);
    }
  }

  // Get data from a specific section
  function getSectionData(sectionName: string): any {
    switch (sectionName) {
      case 'position-details':
        return {
          summary: getTextareaValue('position-summary'),
          source_url: getInputValue('prop-url')
        };
      case 'job-requirements':
        return {
          summary: getTextareaValue('requirements-summary')
        };
      case 'company-information':
        return {
          summary: getTextareaValue('company-summary')
        };
      case 'skills-matrix':
        return {
          summary: getTextareaValue('skills-assessment')
        };
      case 'application-materials':
        return {
          summary: getTextareaValue('materials-summary')
        };
      case 'interview-schedule':
        return {
          summary: getTextareaValue('interview-details')
        };
      case 'interview-preparation':
        return {
          summary: getTextareaValue('preparation-summary')
        };
      case 'communication-log':
        return {
          summary: getTextareaValue('communication-summary')
        };
      case 'key-contacts':
        return {
          summary: getTextareaValue('contacts-summary')
        };
      case 'interview-feedback':
        return {
          summary: getTextareaValue('feedback-summary')
        };
      case 'offer-details':
        return {
          summary: getTextareaValue('offer-summary')
        };
      case 'rejection-analysis':
        return {
          summary: getTextareaValue('rejection-summary')
        };
      case 'privacy-policy':
        return {
          summary: getTextareaValue('privacy-summary')
        };
      case 'lessons-learned':
        return {
          summary: getTextareaValue('lessons-summary')
        };
      case 'performance-metrics':
        return {
          summary: getTextareaValue('metrics-summary')
        };
      case 'advisor-review':
        return {
          summary: getTextareaValue('advisor-summary')
        };
      case 'application-summary':
        return {
          summary: getTextareaValue('overall-summary')
        };
      default:
        return {};
    }
  }

  // Function to get current job application info
  function getCurrentJobInfo(): { id: string | null; url: string | null } {
    return {
      id: jobOpsDataManager.getCurrentJobApplicationId(),
      url: jobOpsDataManager.getCurrentCanonicalUrl()
    };
  }

  
  function setupToggleHandlers() {
    // Add click event listeners to all toggle headers
    const toggleHeaders = document.querySelectorAll('.properties-header, .markdown-header, .realtime-header, .job-header, .console-header');
    toggleHeaders.forEach(header => {
      // Accessibility roles/attributes
      (header as HTMLElement).setAttribute('role', 'button');
      (header as HTMLElement).setAttribute('tabindex', '0');
      (header as HTMLElement).setAttribute('aria-expanded', 'false');
      const toggleTargetInit = (header as HTMLElement).getAttribute('data-toggle');
      if (toggleTargetInit) {
        (header as HTMLElement).setAttribute('aria-controls', toggleTargetInit);
      }

      header.addEventListener('click', (event) => {
        if (event.target && (event.target as Element).closest('button')) return;
        const toggleTarget = (header as HTMLElement).getAttribute('data-toggle');
        if (toggleTarget) {
          toggleSection(toggleTarget);
        }
      });
      // Keyboard support
      (header as HTMLElement).addEventListener('keydown', (e) => {
        const evt = e as KeyboardEvent;
        const toggleTarget = (header as HTMLElement).getAttribute('data-toggle');
        if (!toggleTarget) return;
        if (evt.key === 'Enter' || evt.key === ' ') {
          evt.preventDefault();
          toggleSection(toggleTarget);
        } else if (evt.key === 'ArrowRight') {
          ensureExpanded(toggleTarget);
        } else if (evt.key === 'ArrowLeft') {
          ensureCollapsed(toggleTarget);
        }
      });
    });

    // Expand/Collapse All buttons
    const expandAll = document.getElementById('expand-all');
    const collapseAll = document.getElementById('collapse-all');
    expandAll?.addEventListener('click', () => setAllSections(true));
    collapseAll?.addEventListener('click', () => setAllSections(false));
  }

  function ensureExpanded(sectionId: string) {
    const content = document.getElementById(sectionId);
    if (content && content.classList.contains('collapsed')) toggleSection(sectionId);
  }

  function ensureCollapsed(sectionId: string) {
    const content = document.getElementById(sectionId);
    if (content && content.classList.contains('expanded')) toggleSection(sectionId);
  }

  function setAllSections(expand: boolean) {
    const sectionIds: string[] = [
      'properties-content', 'markdown-content', 'realtime-content', 'console-output',
      'position-details-content', 'job-requirements-content', 'company-information-content',
      'skills-matrix-content', 'application-materials-content', 'interview-schedule-content',
      'interview-preparation-content', 'communication-log-content', 'key-contacts-content',
      'interview-feedback-content', 'offer-details-content', 'rejection-analysis-content',
      'privacy-policy-content', 'lessons-learned-content', 'performance-metrics-content',
      'advisor-review-content', 'application-summary-content'
    ];
    sectionIds.forEach(id => {
      if (expand) ensureExpanded(id); else ensureCollapsed(id);
    });
  }

  // Persist collapse state
  function saveCollapseState(sectionId: string, isCollapsed: boolean) {
    chrome.storage.sync.get(['collapse_state'], (res) => {
      const state = res['collapse_state'] || {};
      state[sectionId] = isCollapsed;
      chrome.storage.sync.set({ collapse_state: state });
    });
  }

  function restoreCollapseState() {
    chrome.storage.sync.get(['collapse_state'], (res) => {
      const state = res['collapse_state'] || {};
      Object.entries(state).forEach(([sectionId, collapsed]) => {
        const content = document.getElementById(sectionId);
        if (!content) return;
        const isCollapsed = !!collapsed;
        const currentlyCollapsed = content.classList.contains('collapsed');
        if (isCollapsed !== currentlyCollapsed) {
          toggleSection(sectionId);
        }
      });
    });
  }

  function toggleSection(sectionId: string) {
    const content = document.getElementById(sectionId);
    if (!content) {
      logToConsole(`❌ Section element not found: ${sectionId}`, "error");
      return;
    }
    const header = content.parentElement?.querySelector('[data-toggle="' + sectionId + '"]');
    const toggleIcon = header?.querySelector('.toggle-icon');
    if (content && header && toggleIcon) {
      const isCollapsed = content.classList.contains('collapsed');
      if (isCollapsed) {
        content.classList.remove('collapsed');
        content.classList.add('expanded');
        (header as HTMLElement).setAttribute('aria-expanded', 'true');
        if (sectionId === 'console-output') {
          toggleIcon.textContent = '▼';
          const consoleMonitor = content.closest('.console-monitor');
          if (consoleMonitor) {
            consoleMonitor.setAttribute('data-collapsed', 'false');
            document.documentElement.style.setProperty('--button-bottom', '208px');
            const form = document.querySelector('#properties-form');
            if (form) (form as HTMLElement).style.paddingBottom = '120px';
          }
          logToApplicationLog('INFO', 'Debug console expanded', { section: sectionId });
        } else {
          toggleIcon.textContent = '▼';
        }
        logToConsole(`✅ Section expanded: ${sectionId}`, "debug");
        saveCollapseState(sectionId, false);
      } else {
        content.classList.remove('expanded');
        content.classList.add('collapsed');
        (header as HTMLElement).setAttribute('aria-expanded', 'false');
        if (sectionId === 'console-output') {
          toggleIcon.textContent = '▶';
          const consoleMonitor = content.closest('.console-monitor');
          if (consoleMonitor) {
            consoleMonitor.setAttribute('data-collapsed', 'true');
            document.documentElement.style.setProperty('--button-bottom', '48px');
            const form = document.querySelector('#properties-form');
            if (form) (form as HTMLElement).style.paddingBottom = '80px';
          }
          logToApplicationLog('INFO', 'Debug console collapsed', { section: sectionId });
        } else {
          toggleIcon.textContent = '▶';
        }
        logToConsole(`✅ Section collapsed: ${sectionId}`, "debug");
        saveCollapseState(sectionId, true);
      }
    } else {
      logToConsole(`❌ Header or toggle icon not found for section: ${sectionId}`, "error");
    }
  }

  // After UI init, restore previous collapse state
  restoreCollapseState();

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
    // Images as thumbnails with CORS error handling - SKIPPED for generate-report workflow
    propImages.innerHTML = '';
    if (Array.isArray(data.images) && data.images.length > 0) {
      // Skip image loading entirely - just show count
      const imageCount = document.createElement('div');
      imageCount.className = 'property-image-count';
      imageCount.textContent = `🖼️ ${data.images.length} images (not loaded)`;
      imageCount.title = 'Images skipped for performance';
      propImages.appendChild(imageCount);
      
      logToConsole(`🖼️ Skipped loading ${data.images.length} images for generate-report workflow`, "info");
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

  const updateJobDataFromFieldsDebounced = debounce(() => updateJobDataFromFields(), 200);

  [propTitle, propUrl, propAuthor, propPublished, propCreated, propDescription, propTags, propLocation].forEach(input => {
    input.addEventListener('input', updateJobDataFromFieldsDebounced);
  });

  async function requestJobData() {
      logToConsole(i18n.getConsoleMessage('requestingJobData'), "info");
    
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]?.id) {
        logToConsole(i18n.getConsoleMessage('noActiveTab'), "error");
        return;
      }
      
      logToConsole(i18n.getConsoleMessage('checkingContentScript'), "debug");
      // On-demand inject the content script using activeTab permission
      chrome.scripting.executeScript(
        {
          target: { tabId: tabs[0].id },
          files: ['content.js']
        },
        async () => {
          if (chrome.runtime.lastError) {
            logToConsole(`❌ Failed to inject content script: ${chrome.runtime.lastError.message}`, 'error');
            return;
          }
          logToConsole('✅ Content script injected', 'success');
          chrome.tabs.sendMessage(
            tabs[0].id!,
            { action: "clip_page" },
            async (response) => {
              if (chrome.runtime.lastError) {
                logToConsole(i18n.getConsoleMessage('cannotConnectToContentScript'), "error");
                return;
              }
              if (response && response.jobData) {
                logToConsole(i18n.getConsoleMessage('jobDataReceived'), "success");
                logToConsole(`📊 Job title: ${response.jobData.title || 'N/A'}`, "info");
                                  logToConsole(`${i18n.getConsoleMessage('jobDataKeys')}: ${Object.keys(response.jobData).join(', ')}`, "debug");
                
                // Ensure we have the essential data
                if (!response.jobData.title && !response.jobData.body) {
                  logToConsole(i18n.getConsoleMessage('jobDataMissingFields'), "warning");
                                      showNotification(i18n.getNotificationMessage('jobDataIncomplete'), true);
                  return;
                }
                
                jobData = response.jobData;
                
                // Check if job application already exists
                const jobExists = await jobOpsDataManager.checkAndLoadExistingJob(jobData.url);
                if (jobExists) {
                  logToConsole(i18n.getConsoleMessage('existingJobFoundAndLoaded'), "info");
                                      showNotification(i18n.getNotificationMessage('existingJobLoaded'));
                  // The populateUIWithData method will dispatch a 'jobDataLoaded' event
                  // which we'll handle below to populate the properties with loaded data
                } else {
                  // Check if we have sufficient content to create a database record
                  const { hasContent, missingSections, contentQuality } = checkRequiredSectionsContent();
                  
                  if (hasContent) {
                    logToConsole(`${i18n.getConsoleMessage('creatingNewJobApplication')} (${i18n.getConsoleMessage('contentQuality')}: ${contentQuality})`, "info");
                    try {
                      await jobOpsDataManager.createNewJobApplication(jobData);
                      showNotification(`🆕 New job application created (${contentQuality} content)`);
                      
                      // Provide enhanced guidance for content improvement
                      validateAndProvideFeedback(contentQuality, missingSections);
                    } catch (error) {
                      logToConsole(`❌ Error creating job application: ${error}`, "error");
                      showNotification("❌ Error creating job application", true);
                    }
                  } else {
                    const minRequirements = missingSections.map(section => {
                      const req = [
                        { name: 'Position Details', minLength: 50 },
                        { name: 'Job Requirements', minLength: 50 },
                        { name: 'Company Information', minLength: 30 },
                        { name: 'Offer Details', minLength: 20 }
                      ].find(s => s.name === section);
                      return `${section} (${req?.minLength || 50}+ chars)`;
                    }).join(', ');
                    
                    logToConsole(`⚠️ Insufficient content for database creation. Missing: ${missingSections.join(', ')}`, "warning");
                  }
                }
                
                // Always populate properties with the scraped data (for new jobs or fallback)
                populatePropertyFields(jobData);
                markdownEditor.value = generateMarkdown(jobData);
                // Copy button is always enabled
                copyBtn.disabled = false;
                
                                      logToConsole(i18n.getConsoleMessage('jobDataPopulated'), "success");
              } else {
                logToConsole(i18n.getConsoleMessage('noJobDataReceived'), "warning");
                                  showNotification(i18n.getNotificationMessage('noJobDataFound'), true);
              }
            }
          );
        }
      );
    });
  }

  // Enhanced copy function with notification - now exports all form data as JSON
  copyBtn.onclick = async () => {
    logToConsole(i18n.getConsoleMessage('copyToClipboardTriggered'), "info");
    
    try {
      // Collect all form data as JSON
      const allFormData = collectAllFormData();
      
      // Check if we have any content to copy
      const hasContent = Object.values(allFormData).some(section => {
        if (typeof section === 'string') {
          return section.trim().length > 0;
        } else if (typeof section === 'object' && section !== null) {
          return Object.values(section).some(value => {
            if (typeof value === 'string') {
              return value.trim().length > 0;
            } else if (typeof value === 'boolean') {
              return value;
            }
            return false;
          });
        }
        return false;
      });
      
      if (!hasContent) {
        logToConsole(i18n.getConsoleMessage('noContentToCopy'), "error");
        showNotification(i18n.getNotificationMessage('noContentToCopy'), true);
        return;
      }

      // Convert to formatted JSON
      const jsonContent = JSON.stringify(allFormData, null, 2);
      
              logToConsole(`${i18n.getConsoleMessage('copyingJsonData')} (${jsonContent.length} characters)...`, "progress");
      await navigator.clipboard.writeText(jsonContent);
      
      // Show success notification
      logToConsole(i18n.getConsoleMessage('allFormDataCopiedSuccess'), "success");
      showNotification(i18n.getNotificationMessage('allFormDataCopied'));
      
    } catch (e) {
      logToConsole(`${i18n.getConsoleMessage('copyFailedWithError')}: ${e}`, "error");
      showNotification(i18n.getNotificationMessage('copyFailed'), true);
    }
  };

  // Notification function using Chrome notifications
  function showNotification(message: string, isError: boolean = false) {
    if (chrome.notifications) {
      const id = `jobops_${Date.now()}`;
      chrome.notifications.create(id, {
        type: "basic",
        iconUrl: "icon.png",
        title: "JobOps Clipper",
        message: message,
        priority: isError ? 2 : 1
      });
      setTimeout(() => chrome.notifications.clear(id), 2500);
    } else {
      logToConsole(message, isError ? "error" : "info");
    }
  }


  // Handle resume upload
  async function handleResumeUpload(event: Event) {
    console.log("🎯 RESUME UPLOAD TRIGGERED - DIRECT CONSOLE LOG");
    logToConsole(i18n.getConsoleMessage('resumeUploadTriggered'), "info");
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    
    if (!file) {
      logToConsole(i18n.getConsoleMessage('noFileSelected'), "error");
      showNotification(i18n.getNotificationMessage('noFileSelected'), true);
      return;
    }

    if (file.type !== 'application/pdf') {
      logToConsole(i18n.getConsoleMessage('invalidFileType'), "error");
      showNotification(i18n.getNotificationMessage('invalidFileType'), true);
      return;
    }

    logToConsole(`📄 Starting PDF extraction: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, "progress");

    try {
      // Step 1: Start extraction
      logToConsole("📄 Loading PDF file...", "progress");
      showNotification("📄 Loading PDF file...");
      logToConsole("📄 Loading PDF file into memory...", "progress");

      // Step 2: Extract content
      logToConsole("🔍 Extracting text content from PDF...", "progress");
      showNotification("🔍 Extracting PDF content...");
      logToConsole("🔍 Extracting text content from PDF...", "progress");
      
      console.log("🎯 ABOUT TO EXTRACT PDF CONTENT - DIRECT CONSOLE LOG");
      resumeContent = await extractPdfContent(file);
      console.log("🎯 PDF EXTRACTION COMPLETED - DIRECT CONSOLE LOG");
      
      logToConsole(`✅ PDF extraction completed! Content length: ${resumeContent.length} characters`, "success");
      logToConsole(`📄 Resume content preview: ${resumeContent.substring(0, 200)}${resumeContent.length > 200 ? '...' : ''}`, "debug");
      logToConsole(`📄 Resume content stored in variable: ${resumeContent ? 'YES' : 'NO'}`, "debug");
      
      // Step 3: Success
      logToConsole(i18n.getConsoleMessage('resumeContentExtracted'), "success");
      logToConsole(i18n.getConsoleMessage('resumeReady'), "success");
      
      // Step 4: Ready for generation
      setTimeout(() => {
        logToConsole(i18n.getConsoleMessage('resumeReady'), "success");
      }, 2000);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logToConsole(`❌ PDF extraction failed: ${errorMessage}`, "error");
      showNotification(`❌ Failed to extract PDF content: ${errorMessage}`, true);
    }
  }

  // Handle generate report
  async function handleGenerateReport() {
    console.log("🎯 GENERATE REPORT BUTTON CLICKED - DIRECT CONSOLE LOG");
    logToConsole(i18n.getConsoleMessage('generateReportClicked'), "info");
    logToConsole(`📊 Current resumeContent length: ${resumeContent.length}`, "debug");
    logToConsole(`📋 Current jobData keys: ${Object.keys(jobData).join(', ')}`, "debug");
    
    if (!resumeContent) {
      logToConsole(i18n.getConsoleMessage('noResumeContent'), "warning");
      // Trigger file upload if no resume content
      resumeUpload.click();
      return;
    }

    // Also check if we have job data
    if (!jobData || Object.keys(jobData).length === 0) {
      logToConsole(i18n.getConsoleMessage('noJobData'), "warning");
      // Wait for job data to be loaded
      await new Promise<void>((resolve) => {
        requestJobData();
        // Give it a moment to load
        setTimeout(() => {
          logToConsole(`📋 After requestJobData - jobData keys: ${Object.keys(jobData).join(', ')}`, "debug");
          logToConsole(`📋 Job data title: ${jobData.title || 'N/A'}`, "debug");
          logToConsole(`📋 Job data body length: ${jobData.body ? jobData.body.length : 0}`, "debug");
          resolve();
        }, 1000);
      });
      
      // Check again after waiting
      if (!jobData || Object.keys(jobData).length === 0) {
        logToConsole(i18n.getConsoleMessage('stillNoJobData'), "error");
        showNotification(i18n.getNotificationMessage('noJobDataAvailable'), true);
        return;
      }
    }
    
    // Verify we have essential data
    if (!jobData.title && !jobData.body) {
      logToConsole(i18n.getConsoleMessage('jobDataIncomplete'), "error");
              showNotification(i18n.getNotificationMessage('jobDataIncomplete'), true);
      return;
    }

    logToConsole(i18n.getConsoleMessage('reportGenerationStarted'), "info");
    generateReportBtn.disabled = true;
    logToConsole("🔄 Starting report generation...", "info");
    showNotification("🔄 Starting report generation...");
    
    // Add immediate test message to verify button click is working
    logToConsole("🎯 BUTTON CLICK VERIFICATION - This should appear immediately", "info");

    try {
      // Step 1: Check API key
      logToConsole("🔑 Checking API configuration...", "progress");
      logToConsole("🔑 Checking API configuration...", "info");
      const apiKey = await getGroqApiKey();
      if (!apiKey) {
        const message = 'Groq API key not configured. Please configure in settings.';
        logToConsole("❌ " + message, "error");
        showNotification(message, true);
        
        // Show native notification with shorter duration
        showNativeNotification('JobOps Clipper - Groq API Configuration', message, 2);
        return;
      }
      logToConsole("✅ API key found, proceeding with report generation", "success");
      showNotification("✅ API key found, proceeding...");

      // Step 2: Prepare data
      logToConsole("📊 Preparing job data and resume content...", "progress");
      logToConsole(`📋 Job data keys: ${Object.keys(jobData).join(', ')}`, "debug");
      logToConsole(`📄 Resume content length: ${resumeContent.length} characters`, "debug");
      logToConsole("📊 Preparing data for analysis...", "info");

      // Step 3: Generate report with streaming
      logToConsole("🤖 Starting streaming report generation...", "progress");
      logToConsole("🤖 Starting streaming report generation...", "info");
      logToConsole("🤖 Starting streaming analysis...", "info");
      
      // Force expand real-time section first
      logToConsole("🔧 Forcing real-time section expansion...", "debug");
      const realtimeContent = document.getElementById("realtime-content");
      if (realtimeContent) {
        if (realtimeContent.classList.contains('collapsed')) {
          toggleSection('realtime-content');
          logToConsole("✅ Real-time section expanded", "debug");
        } else {
          logToConsole("✅ Real-time section already expanded", "debug");
        }
      } else {
        logToConsole("❌ Real-time content element not found", "error");
      }
      
      // Initialize real-time response with test message
      const realtimeResponse = document.getElementById("realtime-response");
      if (realtimeResponse) {
        const safe = DOMPurify.sanitize('<span class="typing-text">🚀 Starting report generation...</span>');
        realtimeResponse.innerHTML = safe;
        realtimeResponse.classList.add('typing');
        logToConsole("✅ Real-time response element initialized with test message", "debug");
      } else {
        logToConsole("❌ Real-time response element not found", "error");
      }
      
      // Show stop generation button
      if (stopGenerationBtn) {
        stopGenerationBtn.style.display = 'inline-block';
        logToConsole("✅ Stop generation button shown", "debug");
      } else {
        logToConsole("❌ Stop generation button not found", "error");
      }
      
      isGenerating = true;
      abortController = new AbortController();
      
      logToConsole("🔄 Calling generateJobReportStreaming...", "debug");
      const report = await generateJobReportStreaming(jobData, resumeContent, (chunk: string) => {
        logToConsole(`📝 Chunk callback received: ${chunk.length} characters`, "debug");
        const realtimeResponse = document.getElementById("realtime-response");
        if (realtimeResponse) {
          const span = document.createElement('span');
          span.className = 'typing-text';
          span.textContent = chunk; // textContent is safe (no HTML)
          realtimeResponse.appendChild(span);
          realtimeResponse.scrollTop = realtimeResponse.scrollHeight;
          logToConsole(`📝 Real-time chunk added to UI: ${chunk.length} characters`, "debug");
        } else {
          logToConsole("❌ Real-time response element not found in chunk callback", "error");
        }
      });
      
      logToConsole(`📊 Report generation result: ${report ? 'success' : 'failed'}`, "debug");
      
      if (!report) {
        throw new Error('No report generated - API returned empty response');
      }
      
      // Step 4: Success
      logToConsole("✅ Report generated successfully!", "success");
      logToConsole("📋 Report ready for copying", "success");
      markdownEditor.value = report;
      
      // Also update real-time response with final content
      if (realtimeResponse) {
        realtimeResponse.classList.remove('typing');
        logToConsole("✅ Real-time response completed", "success");
      }
      
      // Keep success message visible longer
      setTimeout(() => {
        logToConsole("📋 Report ready for copying", "success");
      }, 2000);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logToConsole(`❌ Report generation failed: ${errorMessage}`, "error");
      
      // Clean up streaming state
      isGenerating = false;
      abortController = null;
      
      // Add error message to real-time response
      const realtimeResponse = document.getElementById("realtime-response");
      if (realtimeResponse) {
        realtimeResponse.classList.remove('typing');
        const safe = DOMPurify.sanitize(`<br><span style="color: #ff6b6b;">❌ Error: ${escapeHtml(errorMessage)}</span>`);
        realtimeResponse.innerHTML += safe;
        logToConsole("✅ Error message added to real-time response", "debug");
      }
      if (stopGenerationBtn) {
        stopGenerationBtn.style.display = 'none';
      }
      
      if (errorMessage.includes('API key')) {
        logToConsole("🔧 API key required - please configure in settings", "warning");
        showNotification("❌ Groq API key not configured. Click ⚙️ to set it up.", true);
      } else if (errorMessage.includes('Groq API')) {
        logToConsole("⚠️ Groq API failed, trying Ollama fallback...", "warning");
        showNotification("⚠️ Groq API failed, trying Ollama...");
        try {
          logToConsole("🔄 Attempting Ollama fallback...", "progress");
          const report = await generateJobReportWithOllama(jobData, resumeContent);
          markdownEditor.value = report;
          logToConsole("✅ Report generated with Ollama fallback!", "success");
          showNotification("✅ Report generated with Ollama fallback!");
        } catch (ollamaError) {
          logToConsole("❌ Both Groq and Ollama failed", "error");
          showNotification("❌ Report generation failed on all services", true);
        }
      } else {
        logToConsole("❌ Report generation failed with unknown error", "error");
        showNotification("❌ Report generation failed", true);
      }
    } finally {
      generateReportBtn.disabled = false;
      // Clean up streaming state
      isGenerating = false;
      abortController = null;
      if (realtimeResponse) {
        realtimeResponse.classList.remove('typing');
      }
      if (stopGenerationBtn) {
        stopGenerationBtn.style.display = 'none';
      }
    }
  }

  // Handle settings
  async function handleSettings() {
    logToConsole("⚙️ Settings dialog opened", "info");
    
    const groqApiKey = await getGroqApiKey();
    const linearConfig = await getLinearConfig();

    // Load backend URL
    const backendUrl = await new Promise<string | null>((resolve) => {
      chrome.storage.sync.get(['jobops_backend_url'], (res) => resolve(res['jobops_backend_url'] || null));
    });

    // Load encryption setting (flag only; passphrase not stored)
    const encryptionEnabled = await new Promise<boolean>((resolve) => {
      chrome.storage.sync.get(['db_encryption_enabled'], (res) => resolve(!!res['db_encryption_enabled']));
    });

    const settingsHtml = `
      <div class="settings-container">
        <div class="settings-section">
          <h3>🌐 Backend</h3>
          <div class="settings-input-group">
            <input type="text" id="backend-url" class="settings-input" placeholder="Backend API Base (e.g., http://localhost:8877)" value="${backendUrl || ''}" aria-label="Backend API Base">
          </div>
          <div id="backend-error" class="settings-error"></div>
        </div>

        <div class="settings-section">
          <h3>🔐 Database Encryption (optional)</h3>
          <div class="settings-checkbox-group">
            <label>
              <input id="db-encryption-enabled" type="checkbox" ${encryptionEnabled ? 'checked' : ''}>
              Enable encryption
            </label>
          </div>
          <div class="settings-input-group">
            <input type="password" id="db-encryption-pass" class="settings-input" placeholder="Passphrase (min 8 chars)" aria-label="Encryption Passphrase" ${encryptionEnabled ? '' : 'disabled'}>
            <button id="toggle-db-pass" type="button" class="settings-button">👁️</button>
          </div>
          <div id="db-encryption-error" class="settings-error"></div>
        </div>

        <div class="settings-section">
          <h3>🔑 Groq API Settings</h3>
          <div class="settings-input-group">
            <input type="password" id="groq-api-key" class="settings-input" placeholder="Groq API Key" value="${groqApiKey || ''}" aria-label="Groq API Key">
            <button id="toggle-groq-key" type="button" class="settings-button">👁️</button>
            <button id="test-groq" type="button" class="settings-button">🧪 Test</button>
          </div>
          <div id="groq-key-error" class="settings-error"></div>
        </div>
        
        <div class="settings-section">
          <h3>📤 Linear Integration Settings</h3>
          <div class="settings-input-group">
            <input type="password" id="linear-api-key" class="settings-input" placeholder="Linear API Key" value="${linearConfig?.apiKey || ''}" aria-label="Linear API Key">
            <button id="toggle-linear-key" type="button" class="settings-button">👁️</button>
          </div>
          <div class="settings-input-group">
            <input type="text" id="linear-team-id" class="settings-input" placeholder="Linear Team ID" value="${linearConfig?.teamId || ''}" aria-label="Linear Team ID">
            <input type="text" id="linear-project-id" class="settings-input" placeholder="Linear Project ID (optional)" value="${linearConfig?.projectId || ''}" aria-label="Linear Project ID">
          </div>
          <div class="settings-input-group">
            <input type="text" id="linear-assignee-id" class="settings-input" placeholder="Linear Assignee ID (optional)" value="${linearConfig?.assigneeId || ''}" aria-label="Linear Assignee ID">
            <button id="test-linear" type="button" class="settings-button">🧪 Test</button>
          </div>
          <div id="linear-error" class="settings-error"></div>
        </div>
        
        <div class="settings-actions">
          <button id="export-settings" type="button" class="settings-button">⬇️ Export</button>
          <button id="import-settings" type="button" class="settings-button">⬆️ Import</button>
          <div class="consent-group">
            <label>
              <input id="consent-send" type="checkbox">
              Explicit consent to send data to APIs
            </label>
          </div>
        </div>
        
        <div class="settings-footer">
          <button id="save-settings" class="settings-button primary">Save Settings</button>
          <button id="cancel-settings" class="settings-button danger">Cancel</button>
        </div>
      </div>
    `;

    const modal = document.createElement('div');
    modal.className = 'settings-modal';
    modal.innerHTML = `<div class="settings-modal-content">${settingsHtml}</div>`;
    document.body.appendChild(modal);

    const backendUrlInput = modal.querySelector('#backend-url') as HTMLInputElement;
    const encEnabledInput = modal.querySelector('#db-encryption-enabled') as HTMLInputElement;
    const encPassInput = modal.querySelector('#db-encryption-pass') as HTMLInputElement;
    const groqKeyInput = modal.querySelector('#groq-api-key') as HTMLInputElement;
    const linearKeyInput = modal.querySelector('#linear-api-key') as HTMLInputElement;
    const teamIdInput = modal.querySelector('#linear-team-id') as HTMLInputElement;
    const consentCheckbox = modal.querySelector('#consent-send') as HTMLInputElement;

    modal.querySelector('#toggle-db-pass')?.addEventListener('click', () => {
      encPassInput.type = encPassInput.type === 'password' ? 'text' : 'password';
    });
    encEnabledInput.addEventListener('change', () => {
      encPassInput.disabled = !encEnabledInput.checked;
    });

    chrome.storage.sync.get(['consent_send'], (res) => {
      consentCheckbox.checked = !!res['consent_send'];
    });

    const setError = (id: string, msg: string) => {
      const el = modal.querySelector(id) as HTMLElement;
      if (el) {
        el.textContent = msg;
        el.style.display = msg ? 'block' : 'none';
      }
    };

    const validUrl = (value: string) => {
      try { const u = new URL(value); return !!u.protocol && !!u.host; } catch { return false; }
    };

    backendUrlInput.addEventListener('input', debounce(() => {
      const v = backendUrlInput.value.trim();
      setError('#backend-error', v.length === 0 || validUrl(v) ? '' : 'Invalid URL');
    }, 200));

    // Debounced validation: Linear team id required when API key provided
    const validateLinearConfigDebounced = debounce(() => {
      const key = linearKeyInput?.value.trim() || '';
      const teamId = teamIdInput?.value.trim() || '';
      if (key && !teamId) {
        setError('#linear-error', 'Team ID is required when Linear API key is provided');
      } else {
        setError('#linear-error', '');
      }
    }, 200);

    linearKeyInput?.addEventListener('input', validateLinearConfigDebounced);
    teamIdInput?.addEventListener('input', validateLinearConfigDebounced);

    // Debounced validation: encryption passphrase length when enabled
    const validateEncryptionPassDebounced = debounce(() => {
      const enabled = !!encEnabledInput?.checked;
      const pass = encPassInput?.value.trim() || '';
      if (enabled && (!pass || pass.length < 8)) {
        setError('#db-encryption-error', 'Passphrase must be at least 8 characters');
      } else {
        setError('#db-encryption-error', '');
      }
    }, 200);

    encEnabledInput?.addEventListener('change', validateEncryptionPassDebounced);
    encPassInput?.addEventListener('input', validateEncryptionPassDebounced);

    // Initial run to reflect current values
    validateLinearConfigDebounced();
    validateEncryptionPassDebounced();

    // Save settings
    const saveBtn = modal.querySelector('#save-settings');
    saveBtn?.addEventListener('click', async (event) => {
      event.preventDefault();
      const groqKey = groqKeyInput?.value.trim();
      const linearKey = linearKeyInput?.value.trim();
      const linearTeamId = teamIdInput?.value.trim();
      const linearProjectId = (modal.querySelector('#linear-project-id') as HTMLInputElement)?.value.trim();
      const linearAssigneeId = (modal.querySelector('#linear-assignee-id') as HTMLInputElement)?.value.trim();
      const backend = backendUrlInput?.value.trim();
      const encEnabled = encEnabledInput?.checked;
      const encPass = encPassInput?.value.trim();

      if (backend && !validUrl(backend)) {
        setError('#backend-error', 'Invalid URL');
        return;
      }
      if (linearKey && !linearTeamId) {
        setError('#linear-error', 'Team ID is required when Linear API key is provided');
        return;
      }
      if (encEnabled && (!encPass || encPass.length < 8)) {
        setError('#db-encryption-error', 'Passphrase must be at least 8 characters');
        return;
      }

      const settings: any = { consent_send: !!consentCheckbox.checked };
      if (backend) settings.jobops_backend_url = backend;
      if (groqKey) settings.groq_api_key = groqKey;
      if (linearKey) settings.linear_api_key = linearKey;
      if (linearTeamId) settings.linear_team_id = linearTeamId;
      if (linearProjectId) settings.linear_project_id = linearProjectId;
      if (linearAssigneeId) settings.linear_assignee_id = linearAssigneeId;
      settings.db_encryption_enabled = !!encEnabled;

      await new Promise<void>((resolve) => {
        chrome.storage.sync.set(settings, () => {
          logToConsole("✅ Settings saved successfully!", "success");
          showNotification(i18n.getNotificationMessage('settingsSaved'));
          resolve();
        });
      });

      // Apply encryption setting (passphrase is not stored; configured only for current session)
      try {
        await jobOpsDatabase.configureEncryption(!!encEnabled, encEnabled ? encPass : undefined);
        logToConsole(encEnabled ? '🔐 Database encryption enabled for this session' : '🔓 Database encryption disabled', 'success');
      } catch (e) {
        setError('#db-encryption-error', `Failed to configure encryption: ${e instanceof Error ? e.message : String(e)}`);
        return;
      }

      modal.remove();
      document.removeEventListener('keydown', handleEscape);
    });

    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
        document.removeEventListener('keydown', handleEscape);
        logToConsole("❌ Settings dialog cancelled", "info");
      }
    });

    // Close modal with Escape key
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        modal.remove();
        document.removeEventListener('keydown', handleEscape);
        logToConsole("❌ Settings dialog cancelled", "info");
      }
    };
    document.addEventListener('keydown', handleEscape);

    // Settings export/import handlers
    const exportBtn = modal.querySelector('#export-settings');
    exportBtn?.addEventListener('click', async (event) => {
      event.preventDefault();
      chrome.storage.sync.get(null, (all) => {
        const keysToExport = [
          'jobops_backend_url',
          'groq_api_key',
          'linear_api_key',
          'linear_team_id',
          'linear_project_id',
          'linear_assignee_id',
          'db_encryption_enabled',
          'consent_send'
        ];
        const exported: Record<string, any> = {};
        keysToExport.forEach((k) => {
          if (k in all) exported[k] = all[k];
        });
        const blob = new Blob([JSON.stringify(exported, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `jobops_settings_${new Date().toISOString().slice(0,10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
        logToConsole('✅ Settings exported', 'success');
      });
    });

    const importBtn = modal.querySelector('#import-settings');
    importBtn?.addEventListener('click', async (event) => {
      event.preventDefault();
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.accept = 'application/json';
      fileInput.addEventListener('change', async () => {
        const file = fileInput.files?.[0];
        if (!file) return;
        try {
          const text = await file.text();
          const data = JSON.parse(text);
          const allowedKeys = new Set([
            'jobops_backend_url',
            'groq_api_key',
            'linear_api_key',
            'linear_team_id',
            'linear_project_id',
            'linear_assignee_id',
            'db_encryption_enabled',
            'consent_send'
          ]);
          const sanitized: Record<string, any> = {};
          Object.keys(data || {}).forEach((k) => {
            if (allowedKeys.has(k)) sanitized[k] = data[k];
          });
          await new Promise<void>((resolve) => chrome.storage.sync.set(sanitized, () => resolve()));
          logToConsole('✅ Settings imported', 'success');
          showNotification('✅ Settings imported');
        } catch (e) {
          logToConsole(`❌ Failed to import settings: ${e instanceof Error ? e.message : String(e)}`, 'error');
          showNotification('❌ Failed to import settings', true);
        }
      });
      fileInput.click();
    });

    // Cancel button
    const cancelBtn = modal.querySelector('#cancel-settings');
    cancelBtn?.addEventListener('click', (event) => {
      event.preventDefault();
      modal.remove();
      document.removeEventListener('keydown', handleEscape);
      logToConsole("❌ Settings dialog cancelled", "info");
    });
  }

  // Handle test API (right-click on settings button)
  async function handleTestAPI(event: Event) {
    event.preventDefault();
    logToConsole("🧪 Testing API connectivity...", "info");
    
    try {
      const apiKey = await getGroqApiKey();
      if (!apiKey) {
        logToConsole("❌ No API key configured", "error");
        showNotification("❌ No API key configured", true);
        return;
      }
      
      logToConsole("🔑 API key found, testing Groq API...", "progress");
      const testResponse = await callGroqAPI("Say 'Hello, API test successful!'", (chunk) => {
        logToConsole(`🧪 Test chunk: ${chunk}`, "debug");
      });
      
      if (testResponse) {
        logToConsole("✅ API test successful!", "success");
        showNotification("✅ API test successful!");
      } else {
        logToConsole("❌ API test failed - no response", "error");
        showNotification("❌ API test failed", true);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logToConsole(`❌ API test failed: ${errorMessage}`, "error");
      showNotification(`❌ API test failed: ${errorMessage}`, true);
    }
  }

  // Handle stop generation
  function handleStopGeneration() {
    if (abortController) {
      logToConsole("⏹️ Stopping generation...", "warning");
      abortController.abort();
      isGenerating = false;
      abortController = null;
      
      const stopGenerationBtn = document.getElementById("stop-generation") as HTMLButtonElement;
      const realtimeResponse = document.getElementById("realtime-response") as HTMLDivElement;
      
      if (stopGenerationBtn) {
        stopGenerationBtn.style.display = 'none';
      }
      if (realtimeResponse) {
        realtimeResponse.classList.remove('typing');
      }
      
      logToConsole("✅ Generation stopped", "info");
      showNotification(i18n.getNotificationMessage('generationStopped'));
    }
  }

  // Handle copy real-time response
  async function handleCopyRealtime() {
    const realtimeResponse = document.getElementById("realtime-response") as HTMLDivElement;
    
    if (!realtimeResponse || !realtimeResponse.textContent) {
      logToConsole("❌ No real-time content to copy", "error");
      showNotification(i18n.getNotificationMessage('noContentToCopy'), true);
      return;
    }

    try {
      await navigator.clipboard.writeText(realtimeResponse.textContent);
      logToConsole("✅ Real-time response copied to clipboard", "success");
      showNotification(i18n.getNotificationMessage('copied'));
    } catch (error) {
      logToConsole(`❌ Failed to copy real-time response: ${error}`, "error");
      showNotification(i18n.getNotificationMessage('copyFailed'), true);
    }
  }

  // Helper function for shorter native notifications
  function showNativeNotification(title: string, message: string, priority: number = 1) {
    if (chrome.notifications) {
      const notificationId = `jobops_${Date.now()}`;
      chrome.notifications.create(notificationId, {
        type: 'basic',
        iconUrl: 'icon.png',
        title: title,
        message: message,
        priority: priority
      });
      
      // Auto-dismiss after 2 seconds (3x shorter than default)
      setTimeout(() => {
        chrome.notifications.clear(notificationId);
      }, 2000);
    }
  }

  // Scan for missing API keys and show notifications
  async function scanForMissingApiKeys() {
    logToConsole("🔍 Scanning for missing API keys...", "info");
    
    const groqApiKey = await getGroqApiKey();
    const linearConfig = await getLinearConfig();
    
    const missingKeys = [];
    
    if (!groqApiKey) {
      missingKeys.push('Groq API');
      logToConsole("⚠️ Groq API key not configured", "warning");
    }
    
    if (!linearConfig) {
      missingKeys.push('Linear API');
      logToConsole("⚠️ Linear API key not configured", "warning");
    }
    
    if (missingKeys.length > 0) {
      const message = `Missing API keys: ${missingKeys.join(', ')}. Click ⚙️ to configure.`;
      logToConsole(message, "warning");
      
      // Show native notification with shorter duration
      showNativeNotification('JobOps Clipper - API Configuration', message, 1);
      
      // Also show in-app notification
      showNotification(message, true);
    } else {
      logToConsole("✅ All API keys configured", "success");
    }
  }

    // Linear integration functions
  async function getLinearConfig(): Promise<import('./integration').LinearIntegrationConfig | null> {
    return new Promise((resolve) => {
      chrome.storage.sync.get(['linear_api_key', 'linear_team_id', 'linear_project_id', 'linear_assignee_id'], (result) => {
        if (result.linear_api_key && result.linear_team_id) {
          resolve({
            apiKey: result.linear_api_key,
            teamId: result.linear_team_id,
            projectId: result.linear_project_id || undefined,
            assigneeId: result.linear_assignee_id || undefined,
            autoCreateSubtasks: true,
            defaultPriority: 2
          });
        } else {
          resolve(null);
        }
      });
    });
  }

  let isExportingLinear = false;
  async function handleExportToLinear() {
    if (isExportingLinear) {
      logToConsole('⚠️ Export already in progress', 'warning');
      return;
    }
    isExportingLinear = true;
    try {
      const consent = await new Promise<boolean>((resolve) => {
        chrome.storage.sync.get(['consent_send'], (res) => resolve(!!res['consent_send']));
      });
      if (!consent) {
        logToConsole('❌ Consent is required before sending data to Linear', 'error');
        showNotification(i18n.getNotificationMessage('consentRequired'), true);
        return;
      }
      logToConsole("🚀 Starting Linear export...", "info");
      const currentJobId = jobOpsDataManager.getCurrentJobApplicationId();
      if (!currentJobId) {
        logToConsole("❌ No active job application found", "error");
        const message = "No active job application found. Please clip a job posting first.";
        showNotification(message, true);
        showNativeNotification('JobOps Clipper - No Job Application', message, 2);
        return;
      }

      const alreadyExported = await new Promise<boolean>((resolve) => {
        chrome.storage.sync.get([`linear_mapping_${currentJobId}`], (res) => {
          resolve(!!res[`linear_mapping_${currentJobId}`]);
        });
      });
      if (alreadyExported) {
        logToConsole("⚠️ This job application was already exported to Linear", "warning");
        showNotification("⚠️ Already exported to Linear", true);
        return;
      }

      const baseConfig = await getLinearConfig();
      if (!baseConfig) {
        logToConsole("❌ Linear configuration not found", "error");
        const message = "Linear configuration not found. Please configure Linear settings first.";
        showNotification(message, true);
        showNativeNotification('JobOps Clipper - Linear Configuration', message, 2);
        return;
      }

      const svcForMeta = new LinearIntegrationService(baseConfig, jobOpsDataManager);
      logToConsole("🔗 Testing Linear connection...", "progress");
      const connectionTest = await svcForMeta.testConnection();
      if (!connectionTest) {
        logToConsole("❌ Linear connection test failed", "error");
        const message = "Failed to connect to Linear. Please check your API key and try again.";
        showNotification(message, true);
        showNativeNotification('JobOps Clipper - Linear Connection Failed', message, 2);
        return;
      }
      logToConsole("✅ Linear connection successful", "success");

      // Fetch metadata and let user select project/labels
      const [projects, labels] = await Promise.all([
        svcForMeta.getProjects(baseConfig.teamId),
        svcForMeta.getLabels(baseConfig.teamId)
      ]);

      const selection = await new Promise<{ projectId?: string; labelNames: string[] }>((resolve) => {
        const modal = document.createElement('div');
        modal.style.cssText = 'position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.5);z-index:10001;';
        const projOptions = ["<option value=\"\">(None)</option>", ...projects.map(p => `<option value="${p.id}">${p.name}</option>`)].join('');
        const labelOptions = labels.map(l => `<label style="display:inline-flex;align-items:center;gap:6px;margin:4px 8px 4px 0;"><input type="checkbox" value="${l.name}"> ${l.name}</label>`).join('');
        modal.innerHTML = `
          <div style="background:#fff;border-radius:8px;padding:16px 16px;min-width:360px;max-width:560px;">
            <h3 style="margin:0 0 8px 0;">Linear Export Options</h3>
            <label>Project:
              <select id="linear-project-select" style="width:100%;padding:6px;margin-top:4px;">${projOptions}</select>
            </label>
            <div style="margin-top:12px;">
              <div style="margin-bottom:6px;">Labels:</div>
              <div id="linear-labels-list" style="display:flex;flex-wrap:wrap;">${labelOptions}</div>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
              <button id="cancel-export" type="button" style="padding:8px 12px;">Cancel</button>
              <button id="confirm-export" type="button" style="padding:8px 12px;background:#4CAF50;color:#fff;border:none;border-radius:4px;">Export</button>
            </div>
          </div>`;
        document.body.appendChild(modal);
        modal.querySelector('#cancel-export')?.addEventListener('click', () => {
          document.body.removeChild(modal);
          resolve({ projectId: undefined, labelNames: [] });
        });
        modal.querySelector('#confirm-export')?.addEventListener('click', () => {
          const projectId = (modal.querySelector('#linear-project-select') as HTMLSelectElement).value || undefined;
          const selected: string[] = Array.from(modal.querySelectorAll('#linear-labels-list input[type="checkbox"]:checked')).map((el: any) => el.value);
          document.body.removeChild(modal);
          resolve({ projectId, labelNames: selected });
        });
      });

      const config: any = { ...baseConfig };
      if (selection.projectId) config.projectId = selection.projectId;
      if (selection.labelNames && selection.labelNames.length > 0) config.additionalLabels = selection.labelNames;

      const linearService = new LinearIntegrationService(config, jobOpsDataManager);
      logToConsole("📤 Exporting job application to Linear...", "progress");
      const result = await linearService.exportJobToLinear(currentJobId);

      if (result.success) {
        chrome.storage.sync.set({ [`linear_mapping_${currentJobId}`]: result.mainTask?.id || true });
        logToConsole("✅ Job exported to Linear successfully", "success");
        if (result.failedSubtasks && result.failedSubtasks.length > 0) {
          logToConsole(`⚠️ ${result.failedSubtasks.length} subtasks failed to create`, 'warning');
          for (const f of result.failedSubtasks) {
            logToConsole(`• ${f.section}: ${f.error}`, 'warning');
          }
        }
        const message = `Job exported to Linear! Created 1 main task and ${result.subtasks.length} subtasks.`;
        showNotification(message);
        if (result.mainTask.url) {
          chrome.tabs.create({ url: result.mainTask.url });
        }
      } else {
        logToConsole(`❌ Linear export failed: ${result.error}`, "error");
        showNotification(`Failed to export to Linear: ${result.error}`, true);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logToConsole(`❌ Linear export error: ${errorMessage}`, "error");
      showNotification(`Linear export failed: ${errorMessage}`, true);
    } finally {
      isExportingLinear = false;
    }
  }

    // Global error boundary for popup
  window.addEventListener('error', (event) => {
    const message = event?.message || 'Unknown runtime error';
    logToConsole(`❌ Uncaught error: ${message}`, 'error');
    showNotification('❌ An unexpected error occurred. See console for details.', true);
  });
  window.addEventListener('unhandledrejection', (event) => {
    const reason = (event.reason instanceof Error ? event.reason.message : String(event.reason || 'Unknown'));
    logToConsole(`❌ Unhandled promise rejection: ${reason}`, 'error');
    showNotification('❌ A background error occurred. Some actions may not have completed.', true);
  });
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

// Extract PDF content using Groq API for reliable parsing
async function extractPdfContent(file: File): Promise<string> {
  return new Promise(async (resolve, reject) => {
    logToConsole("🔄 Starting PDF content extraction with Groq API...", "progress");
    
    try {
      // Check if Groq API key is available
      const apiKey = await getGroqApiKey();
      if (!apiKey) {
        logToConsole("❌ No Groq API key available for PDF parsing", "error");
        const manualText = prompt("Groq API key not configured. Please paste your resume content manually:");
        if (manualText && manualText.trim().length > 10) {
          logToConsole("✅ Manual resume content provided", "success");
          resolve(manualText.trim());
        } else {
          reject(new Error('No resume content available'));
        }
        return;
      }
      
      const reader = new FileReader();
      reader.onload = async function(e) {
        try {
          logToConsole("📖 File read successfully, converting to base64...", "debug");
          const typedarray = new Uint8Array(e.target?.result as ArrayBuffer);
          logToConsole(`📊 File size: ${typedarray.length} bytes`, "debug");
          
          // Verify the file content looks like a PDF
          const header = new TextDecoder().decode(typedarray.slice(0, 10));
          logToConsole(`📄 File header: ${header}`, "debug");
          if (!header.includes('%PDF')) {
            logToConsole("⚠️ File doesn't appear to be a valid PDF", "warning");
          }
          
          // Convert to base64 for API transmission
          const base64Data = btoa(String.fromCharCode(...typedarray));
          logToConsole("🔄 Converting PDF to base64 for API transmission...", "progress");
          
          // Use Groq API to parse PDF content
          const pdfText = await parsePdfWithGroq(base64Data, file.name);
          
          if (pdfText && pdfText.length > 50) {
            logToConsole(`✅ Groq API PDF parsing successful: ${pdfText.length} characters`, "success");
            resolve(pdfText);
          } else {
            logToConsole("⚠️ Groq API parsing found minimal text, offering manual input", "warning");
            const manualText = prompt("PDF parsing found minimal text. Please paste your resume content manually:");
            if (manualText && manualText.trim().length > 10) {
              logToConsole("✅ Manual resume content provided", "success");
              resolve(manualText.trim());
            } else {
              reject(new Error('No resume content available'));
            }
          }
          
        } catch (error) {
          logToConsole(`❌ Error in PDF processing: ${error}`, "error");
          // Fallback to manual input
          const manualText = prompt("PDF processing failed. Please paste your resume content manually:");
          if (manualText && manualText.trim().length > 10) {
            logToConsole("✅ Manual resume content provided", "success");
            resolve(manualText.trim());
          } else {
            reject(new Error('No resume content available'));
          }
        }
      };
      reader.onerror = (error) => {
        logToConsole(`❌ FileReader error: ${error}`, "error");
        reject(new Error('Failed to read file'));
      };
      reader.readAsArrayBuffer(file);
      
    } catch (error) {
      logToConsole(`❌ Error in PDF extraction setup: ${error}`, "error");
      reject(error);
    }
  });
}

// Parse PDF content using Groq API
async function parsePdfWithGroq(base64Data: string, fileName: string): Promise<string> {
  try {
    logToConsole("🤖 Sending PDF to Groq API for parsing...", "progress");
    
    const apiKey = await getGroqApiKey();
    if (!apiKey) {
      throw new Error('No Groq API key available');
    }
    
    const prompt = `You are an expert PDF parser. I will provide you with a base64-encoded PDF file. Please extract all the text content from this PDF and return it as clean, readable text.

PDF File: ${fileName}
Base64 Data: ${base64Data}

Instructions:
1. Decode the base64 data to access the PDF content
2. Extract all text content from the PDF
3. Preserve the structure and formatting as much as possible
4. Remove any PDF artifacts or formatting codes
5. Return only the clean, readable text content
6. If the PDF contains images with text, describe the text content
7. If the PDF is mostly images, describe what you can see

Please extract and return the text content from this PDF:`;

    logToConsole("📤 Sending PDF parsing request to Groq API...", "progress");
    
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
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.1,
        max_tokens: 4000,
        stream: false
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`Groq API error: ${response.status} - ${JSON.stringify(errorData)}`);
    }

    const data = await response.json();
    const extractedText = data.choices?.[0]?.message?.content;
    
    if (!extractedText) {
      throw new Error('No content received from Groq API');
    }
    
    logToConsole(`✅ Groq API successfully parsed PDF: ${extractedText.length} characters`, "success");
    return extractedText.trim();
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    logToConsole(`❌ Groq API PDF parsing failed: ${errorMessage}`, "error");
    throw error;
  }
}



// Generate comprehensive job report using LLM with streaming
async function generateJobReportStreaming(jobData: Record<string, any>, resumeContent: string, onChunk?: (chunk: string) => void): Promise<string> {
  // Remove images from job data to avoid any image-related issues
  const cleanJobData = { ...jobData };
  if (cleanJobData.images) {
    delete cleanJobData.images;
  }
  
  const prompt = `You are an expert job application analyst. Based on the provided job posting data and resume content, generate a comprehensive job application tracking report.

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
    // Try Groq first with streaming
    logToConsole("🤖 Attempting Groq API with streaming...", "progress");
    const groqResponse = await callGroqAPI(prompt, onChunk);
    if (groqResponse) {
      logToConsole("✅ Groq API succeeded with streaming", "success");
      return groqResponse;
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    logToConsole(`⚠️ Groq API failed: ${errorMessage}`, "warning");
    logToConsole("🔄 Falling back to Ollama...", "progress");
    
    try {
      // Try Ollama as fallback
      logToConsole("🤖 Attempting Ollama API fallback...", "progress");
      const ollamaResponse = await callOllamaAPI(prompt);
      if (ollamaResponse) {
        logToConsole("✅ Ollama API succeeded", "success");
        return ollamaResponse;
      }
    } catch (ollamaError) {
      const ollamaErrorMessage = ollamaError instanceof Error ? ollamaError.message : String(ollamaError);
      logToConsole(`❌ Ollama API also failed: ${ollamaErrorMessage}`, "error");
    }
  }

  logToConsole("❌ Both Groq and Ollama APIs failed", "error");
  throw new Error('Both Groq and Ollama APIs failed');
}

// Generate comprehensive job report using LLM (non-streaming version for backward compatibility)
async function generateJobReport(jobData: Record<string, any>, resumeContent: string): Promise<string> {
  return generateJobReportStreaming(jobData, resumeContent);
}

// Generate report using only Ollama (for fallback)
async function generateJobReportWithOllama(jobData: Record<string, any>, resumeContent: string): Promise<string> {
  // Remove images from job data to avoid any image-related issues
  const cleanJobData = { ...jobData };
  if (cleanJobData.images) {
    delete cleanJobData.images;
  }
  
  const prompt = `You are an expert job application analyst. Based on the provided job posting data and resume content, generate a comprehensive job application tracking report.

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

  const ollamaResponse = await callOllamaAPI(prompt);
  if (ollamaResponse) {
    return ollamaResponse;
  }

  throw new Error('Ollama API failed');
}

// Call Groq API with streaming support
async function callGroqAPI(prompt: string, onChunk?: (chunk: string) => void): Promise<string | null> {
  try {
    await ensureConsent();
    logToConsole("🔑 Retrieving Groq API key from storage...", "debug");
    
    // Get API key from storage or environment
    const apiKey = await getGroqApiKey();
    if (!apiKey) {
      logToConsole("❌ No Groq API key found in storage", "error");
      throw new Error('Groq API key not configured');
    }
    
    logToConsole("✅ Groq API key retrieved successfully", "debug");
    logToConsole(`🌐 Preparing request to Groq API: ${GROQ_API_URL}`, "debug");
    logToConsole(`🤖 Using model: ${GROQ_MODEL}`, "debug");
    logToConsole(`📝 Prompt length: ${prompt.length} characters`, "debug");
    
    const requestBody = {
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
      stream: onChunk ? true : false
    };
    
    logToConsole("📤 Sending request to Groq API...", "debug");
    logToConsole(`📊 Request payload size: ${JSON.stringify(requestBody).length} characters`, "debug");
    logToConsole(`🔄 Streaming mode: ${onChunk ? 'enabled' : 'disabled'}`, "debug");
    
    const startTime = Date.now();
    const response = await fetch(GROQ_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
      signal: abortController?.signal
    });
    
    const endTime = Date.now();
    const responseTime = endTime - startTime;
    
    logToConsole(`⏱️ Response received in ${responseTime}ms`, "debug");
    logToConsole(`📡 HTTP Status: ${response.status} ${response.statusText}`, "debug");
    logToConsole(`📋 Response headers: ${JSON.stringify(Object.fromEntries(response.headers.entries()))}`, "debug");

    if (!response.ok) {
      const errorText = await response.text();
      logToConsole(`❌ Groq API error response: ${errorText}`, "error");
      throw new Error(`Groq API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    // Handle streaming response
    if (onChunk && requestBody.stream) {
      logToConsole("🔄 Processing streaming response...", "debug");
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';
      
      if (!reader) {
        throw new Error('Response body reader not available');
      }
      
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') {
                logToConsole("✅ Streaming completed", "success");
                return fullResponse;
              }
              
              try {
                const parsed = JSON.parse(data);
                if (parsed.choices && parsed.choices[0]?.delta?.content) {
                  const content = parsed.choices[0].delta.content;
                  fullResponse += content;
                  onChunk(content);
                  logToConsole(`📝 Streamed chunk: ${content.length} characters`, "debug");
                }
              } catch (e) {
                // Ignore parsing errors for incomplete chunks
                logToConsole(`⚠️ Ignoring malformed chunk: ${e}`, "debug");
              }
            }
          }
        }
        
        logToConsole(`✅ Streaming completed, total: ${fullResponse.length} characters`, "success");
        return fullResponse;
      } finally {
        reader.releaseLock();
      }
    } else {
      // Handle non-streaming response
      logToConsole("📥 Processing non-streaming response...", "debug");
      const data = await response.json();
      
      logToConsole(`📊 Response data keys: ${Object.keys(data).join(', ')}`, "debug");
      logToConsole(`🎯 Choices count: ${data.choices?.length || 0}`, "debug");
      
      if (data.choices && data.choices.length > 0) {
        const content = data.choices[0]?.message?.content;
        if (content) {
          logToConsole(`✅ Successfully extracted response content (${content.length} characters)`, "success");
          logToConsole(`📝 Response preview: ${content.substring(0, 200)}${content.length > 200 ? '...' : ''}`, "debug");
          return content;
        } else {
          logToConsole("⚠️ Response content is empty or undefined", "warning");
          logToConsole(`🔍 Full response structure: ${JSON.stringify(data, null, 2)}`, "debug");
          return null;
        }
      } else {
        logToConsole("⚠️ No choices found in response", "warning");
        logToConsole(`🔍 Full response structure: ${JSON.stringify(data, null, 2)}`, "debug");
        return null;
      }
    }
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    const errorStack = error instanceof Error ? error.stack : 'No stack trace available';
    
    logToConsole(`❌ Groq API call failed: ${errorMessage}`, "error");
    logToConsole(`🔍 Error stack trace: ${errorStack}`, "debug");
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      logToConsole("🌐 Network error detected - check internet connection", "error");
    } else if (error instanceof SyntaxError) {
      logToConsole("📝 JSON parsing error - invalid response format", "error");
    }
    
    return null;
  }
}

// Call Ollama API (fallback)
async function callOllamaAPI(prompt: string): Promise<string | null> {
  try {
    logToConsole("🔄 Preparing Ollama API fallback request...", "debug");
    logToConsole(`🌐 Ollama URL: ${OLLAMA_URL}/api/generate`, "debug");
    logToConsole(`🤖 Using model: ${OLLAMA_MODEL}`, "debug");
    logToConsole(`📝 Prompt length: ${prompt.length} characters`, "debug");
    
    const requestBody = {
      model: OLLAMA_MODEL,
      prompt: prompt,
      stream: false
    };
    
    logToConsole("📤 Sending request to Ollama API...", "debug");
    logToConsole(`📊 Request payload size: ${JSON.stringify(requestBody).length} characters`, "debug");
    
    const startTime = Date.now();
    const response = await fetch(`${OLLAMA_URL}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });
    
    const endTime = Date.now();
    const responseTime = endTime - startTime;
    
    logToConsole(`⏱️ Ollama response received in ${responseTime}ms`, "debug");
    logToConsole(`📡 HTTP Status: ${response.status} ${response.statusText}`, "debug");
    logToConsole(`📋 Response headers: ${JSON.stringify(Object.fromEntries(response.headers.entries()))}`, "debug");

    if (!response.ok) {
      const errorText = await response.text();
      logToConsole(`❌ Ollama API error response: ${errorText}`, "error");
      throw new Error(`Ollama API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    logToConsole("📥 Parsing Ollama JSON response...", "debug");
    const data = await response.json();
    
    logToConsole(`📊 Ollama response data keys: ${Object.keys(data).join(', ')}`, "debug");
    
    if (data.response) {
      logToConsole(`✅ Successfully extracted Ollama response content (${data.response.length} characters)`, "success");
      logToConsole(`📝 Ollama response preview: ${data.response.substring(0, 200)}${data.response.length > 200 ? '...' : ''}`, "debug");
      return data.response;
    } else {
      logToConsole("⚠️ Ollama response content is empty or undefined", "warning");
      logToConsole(`🔍 Full Ollama response structure: ${JSON.stringify(data, null, 2)}`, "debug");
      return null;
    }
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    const errorStack = error instanceof Error ? error.stack : 'No stack trace available';
    
    logToConsole(`❌ Ollama API call failed: ${errorMessage}`, "error");
    logToConsole(`🔍 Ollama error stack trace: ${errorStack}`, "debug");
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      logToConsole("🌐 Ollama network error detected - check if Ollama is running locally", "error");
    } else if (error instanceof SyntaxError) {
      logToConsole("📝 Ollama JSON parsing error - invalid response format", "error");
    }
    
    return null;
  }
}

// Get Groq API key from Chrome storage
async function getGroqApiKey(): Promise<string | null> {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['groq_api_key'], (result) => {
      const apiKey = result.groq_api_key || null;
      if (apiKey) {
        logToConsole(`🔑 API key found (${apiKey.substring(0, 8)}...)`, "debug");
      } else {
        logToConsole("❌ No API key found in storage", "debug");
      }
      resolve(apiKey);
    });
  });
}

// Consent enforcement for external API calls
async function ensureConsent(): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    try {
      chrome.storage.sync.get(['consent_send'], (res) => {
        const consent = !!res['consent_send'];
        if (consent) resolve();
        else reject(new Error('Consent required before calling Groq API'));
      });
    } catch (e) {
      reject(new Error('Consent check failed'));
    }
  });
}