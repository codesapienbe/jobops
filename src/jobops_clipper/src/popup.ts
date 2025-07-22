// src/popup.ts

document.addEventListener("DOMContentLoaded", async () => {
  let jobData: Record<string, any> = {};

  // Helper to render preview if jobData is available
  function tryRenderPreview() {
    if (jobData && Object.keys(jobData).length > 0) {
      renderPreview(jobData);
    }
  }

  // Listen for preview data from content script
  chrome.runtime.onMessage.addListener((msg, _sender, _sendResponse) => {
    if (msg.action === "show_preview" && msg.jobData) {
      jobData = msg.jobData;
      renderPreview(jobData);
    }
  });

  // Request job data from the content script on popup open
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]?.id) return;
    chrome.tabs.sendMessage(
      tabs[0].id,
      { action: "clip_page" },
      (response) => {
        // If the content script responds with jobData, render it
        if (response && response.jobData) {
          jobData = response.jobData;
          renderPreview(jobData);
        }
      }
    );
  });

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
  };

  (document.getElementById("cancel") as HTMLButtonElement).onclick = () => window.close();
});

function renderPreview(jobData: Record<string, any>) {
  const container = document.getElementById("preview-container") || document.createElement("div");
  container.id = "preview-container";
  let html = '<div class="jobops-preview">';
  for (const [key, value] of Object.entries(jobData)) {
    if (Array.isArray(value) && value.length === 0) continue;
    if (!value || String(value).trim() === "") continue;
    html += `<div class="field"><span class="label">${key}:</span> <span class="value">${Array.isArray(value) ? JSON.stringify(value) : value}</span></div>`;
  }
  html += '</div>';
  container.innerHTML = html;
  // Replace or append preview
  const parent = document.querySelector(".glassmorphic-popup") || document.body;
  let old = document.getElementById("preview-container");
  if (old) old.replaceWith(container); else parent.insertBefore(container, parent.firstChild);
}
