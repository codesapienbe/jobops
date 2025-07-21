/// <reference types="chrome" />
import { BACKEND_API_BASE } from "./config";

function log(...args: any[]) {
  console.log("[JobOps Clipper]", ...args);
}

function showNotification(message: string, isError: boolean = false) {
  chrome.notifications?.create({
    type: "basic",
    iconUrl: "icon.png",
    title: "JobOps Clipper",
    message: message,
    priority: 2
  });
}

async function tryClipPage(tabId: number, attempt = 1, maxAttempts = 3): Promise<any> {
  return new Promise((resolve, reject) => {
    log(`Sending clip_page message to tab ${tabId}, attempt ${attempt}`);
    let responded = false;
    chrome.tabs.sendMessage(tabId, { action: "clip_page" }, (response) => {
      responded = true;
      if (chrome.runtime.lastError) {
        log("chrome.runtime.lastError:", chrome.runtime.lastError);
        if (attempt < maxAttempts) {
          setTimeout(() => {
            tryClipPage(tabId, attempt + 1, maxAttempts).then(resolve).catch(reject);
          }, 500);
        } else {
          showNotification("Failed to extract content from page after multiple attempts.", true);
          reject(chrome.runtime.lastError);
        }
        return;
      }
      if (!response || response.error || !response.title || !response.body) {
        log("Malformed or error response from content script:", response);
        if (attempt < maxAttempts) {
          setTimeout(() => {
            tryClipPage(tabId, attempt + 1, maxAttempts).then(resolve).catch(reject);
          }, 500);
        } else {
          showNotification("No content extracted or malformed response after multiple attempts.", true);
          reject(response && response.error ? response.error : "Malformed response");
        }
        return;
      }
      log("Successfully extracted content:", { title: response.title, url: response.url, bodyLength: response.body.length });
      resolve(response);
    });
    // Fallback: if no response after 2 seconds, treat as failure
    setTimeout(() => {
      if (!responded) {
        log("No response from content script after timeout.");
        if (attempt < maxAttempts) {
          tryClipPage(tabId, attempt + 1, maxAttempts).then(resolve).catch(reject);
        } else {
          showNotification("Content script did not respond after multiple attempts.", true);
          reject("Timeout waiting for content script response");
        }
      }
    }, 2000);
  });
}

// Compatibility and environment checks for Manifest V3 background service worker
try {
  // Check for service worker context
  if (typeof self === 'undefined' || typeof importScripts === 'undefined') {
    // Not running in a service worker
    console.error('[JobOps Clipper] Not running in a service worker context.');
  }

  // Check for Chrome APIs
  if (typeof chrome === 'undefined' || !chrome.action || !chrome.notifications || !chrome.tabs) {
    console.error('[JobOps Clipper] Required Chrome APIs are missing.');
  }

  // Check for icon asset (cannot check file existence directly, but log the expected path)
  const ICON_PATH = 'icon.png';
  // Log manifest version and background script context
  if (chrome && chrome.runtime && chrome.runtime.getManifest) {
    const manifest = chrome.runtime.getManifest();
    console.log(`[JobOps Clipper] Loaded in Chrome extension:`, manifest.name, manifest.version, 'Manifest v' + manifest.manifest_version);
    if (!manifest.background || !("service_worker" in manifest.background)) {
      console.error('[JobOps Clipper] Manifest background.service_worker is missing or misconfigured.');
    }
  } else {
    console.warn('[JobOps Clipper] Unable to access manifest metadata.');
  }

  // Defensive event registration
  if (chrome && chrome.action && chrome.action.onClicked) {
    chrome.action.onClicked.addListener((tab: chrome.tabs.Tab) => {
      if (tab.id !== undefined) {
        try {
          tryClipPage(tab.id).then(async (response) => {
            // Step 1: Store job description
            try {
              const jobDescRes = await fetch(`${BACKEND_API_BASE}/job-description`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  job_markdown: response.body,
                  url: response.url,
                  title: response.title
                })
              });
              if (!jobDescRes.ok) {
                let errMsg = "Unknown error";
                try {
                  const err = await jobDescRes.json();
                  errMsg = err.error || errMsg;
                } catch (err) {
                  log("Error parsing backend error response:", err);
                }
                showNotification(`Error storing job: ${errMsg}`, true);
                return;
              }
              const jobDescData = await jobDescRes.json();
              const groupId = jobDescData.group_id;
              if (!groupId) {
                showNotification("No group_id returned from backend.", true);
                return;
              }
              showNotification("Job description stored. Generating letter...");
              // Step 2: Generate letter
              const genLetterRes = await fetch(`${BACKEND_API_BASE}/generate-letter`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ group_id: groupId })
              });
              if (!genLetterRes.ok) {
                let errMsg = "Unknown error";
                try {
                  const err = await genLetterRes.json();
                  errMsg = err.error || errMsg;
                } catch (err) {
                  log("Error parsing backend error response:", err);
                }
                showNotification(`Error generating letter: ${errMsg}`, true);
                return;
              }
              showNotification("Motivation letter generated successfully!");
            } catch (e) {
              log("Fetch to backend failed:", e);
              showNotification("Failed to communicate with backend.", true);
            }
          }).catch((err) => {
            log("Final failure after retries:", err);
          });
        } catch (e) {
          log("Unexpected error in onClicked handler:", e);
          showNotification("Unexpected error occurred.", true);
        }
      } else {
        log("No active tab found.");
        showNotification("No active tab found.", true);
      }
    });
  } else {
    console.error('[JobOps Clipper] chrome.action.onClicked is not available.');
  }

  // Minimal background worker test for verification
  try {
    console.log('[JobOps Clipper] background.ts loaded and running.');
    self.addEventListener('install', () => {
      console.log('[JobOps Clipper] Service worker installed.');
    });
    self.addEventListener('activate', () => {
      console.log('[JobOps Clipper] Service worker activated.');
    });
  } catch (e) {
    console.error('[JobOps Clipper] Service worker lifecycle event error:', e);
  }

} catch (fatal) {
  console.error('[JobOps Clipper] Fatal error in background script:', fatal);
} 