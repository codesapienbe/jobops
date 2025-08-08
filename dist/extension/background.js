"use strict";
(() => {
  // src/background.ts
  function log(...args) {
    console.log("[JobOps Clipper]", ...args);
  }
  function showNotification(message, isError = false) {
    chrome.notifications?.create({
      type: "basic",
      iconUrl: "icon.png",
      title: "JobOps Clipper",
      message,
      priority: 2
    });
  }
  async function tryClipPage(tabId, attempt = 1, maxAttempts = 3) {
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
            showNotification("Failed to extract content from page after multiple attempts. Please refresh the page and try again.", true);
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
            showNotification("No content extracted or malformed response after multiple attempts. Please refresh the page and try again.", true);
            reject(response && response.error ? response.error : "Malformed response");
          }
          return;
        }
        log("Successfully extracted content:", { title: response.title, url: response.url, bodyLength: response.body.length });
        resolve(response);
      });
      setTimeout(() => {
        if (!responded) {
          log("No response from content script after timeout.");
          if (attempt < maxAttempts) {
            tryClipPage(tabId, attempt + 1, maxAttempts).then(resolve).catch(reject);
          } else {
            showNotification("Content script did not respond after multiple attempts. Please refresh the page and try again.", true);
            reject("Timeout waiting for content script response");
          }
        }
      }, 2e3);
    });
  }
  function getBackendApiBase() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(["jobops_backend_url"], (result) => {
        resolve(result["jobops_backend_url"] || null);
      });
    });
  }
  try {
    if (typeof self === "undefined" || typeof importScripts === "undefined") {
      console.error("[JobOps Clipper] Not running in a service worker context.");
    }
    if (chrome && chrome.runtime && chrome.runtime.onMessage) {
      chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
        if (message && message.action === "ping") {
          sendResponse("pong");
          return true;
        }
        return false;
      });
    }
    if (typeof chrome === "undefined" || !chrome.action || !chrome.notifications || !chrome.tabs) {
      console.error("[JobOps Clipper] Required Chrome APIs are missing.");
    }
    const ICON_PATH = "icon.png";
    if (chrome && chrome.runtime && chrome.runtime.getManifest) {
      const manifest = chrome.runtime.getManifest();
      console.log(`[JobOps Clipper] Loaded in Chrome extension:`, manifest.name, manifest.version, "Manifest v" + manifest.manifest_version);
      if (!manifest.background || !("service_worker" in manifest.background)) {
        console.error("[JobOps Clipper] Manifest background.service_worker is missing or misconfigured.");
      }
    } else {
      console.warn("[JobOps Clipper] Unable to access manifest metadata.");
    }
    if (chrome && chrome.action && chrome.action.onClicked) {
      chrome.action.onClicked.addListener((tab) => {
        const tabIdNum = typeof tab.id === "number" ? tab.id : void 0;
        if (tabIdNum !== void 0) {
          try {
            chrome.scripting.executeScript({ target: { tabId: tabIdNum }, files: ["content.js"] }, () => {
              tryClipPage(tabIdNum).then(async (response) => {
                try {
                  const backendApiBase = await getBackendApiBase();
                  if (!backendApiBase) {
                    showNotification("Backend URL not configured. Please check settings.", true);
                    return;
                  }
                  const clipRes = await fetch(`${backendApiBase}/clip`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      title: response.title,
                      url: response.url,
                      body: response.body
                    })
                  });
                  if (!clipRes.ok) {
                    let errMsg = "Unknown error";
                    try {
                      const err = await clipRes.json();
                      errMsg = err.error || errMsg;
                    } catch (err) {
                      log("Error parsing backend error response:", err);
                    }
                    showNotification(`Error saving clip: ${errMsg}`, true);
                    return;
                  }
                  showNotification("Clip saved successfully!");
                } catch (e) {
                  log("Fetch to backend failed:", e);
                  showNotification("Failed to communicate with backend. Please check your connection.", true);
                }
              }).catch((err) => {
                log("Final failure after retries:", err);
              });
            });
          } catch (e) {
            log("Unexpected error in onClicked handler:", e);
            showNotification("Unexpected error occurred.", true);
          }
        } else {
          log("No active tab found.");
          showNotification("No active tab found. Please open a webpage and try again.", true);
        }
      });
    } else {
      console.error("[JobOps Clipper] chrome.action.onClicked is not available.");
    }
    try {
      console.log("[JobOps Clipper] background.ts loaded and running.");
      self.addEventListener("install", () => {
        console.log("[JobOps Clipper] Service worker installed.");
      });
      self.addEventListener("activate", () => {
        console.log("[JobOps Clipper] Service worker activated.");
      });
    } catch (e) {
      console.error("[JobOps Clipper] Service worker lifecycle event error:", e);
    }
  } catch (fatal) {
    console.error("[JobOps Clipper] Fatal error in background script:", fatal);
  }
})();
//# sourceMappingURL=background.js.map
