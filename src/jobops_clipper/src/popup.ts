// src/popup.ts

import { BACKEND_API_BASE } from "./config";

document.addEventListener("DOMContentLoaded", async () => {
  // Request content from the active tab
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]?.id) return;
    chrome.tabs.sendMessage(
      tabs[0].id,
      { action: "clip_page" },
      (response) => {
        if (!response || response.error) {
          (document.getElementById("clip-status") as HTMLElement).textContent = "Failed to extract content.";
          return;
        }
        (document.getElementById("clip-title") as HTMLElement).textContent = response.title || "";
        (document.getElementById("clip-url") as HTMLElement).textContent = response.url || "";
        (document.getElementById("clip-body") as HTMLTextAreaElement).value = response.body || "";
        (document.getElementById("clip-meta") as HTMLElement).textContent =
          (response.metaDescription ? "Description: " + response.metaDescription + " " : "") +
          (response.ogTitle ? "OG Title: " + response.ogTitle + " " : "") +
          (response.ogSiteName ? "Site: " + response.ogSiteName : "");
        // Store for later
        (window as any)._clipData = response;
      }
    );
  });

  (document.getElementById("approve") as HTMLButtonElement).onclick = async () => {
    const data = (window as any)._clipData || {};
    data.body = (document.getElementById("clip-body") as HTMLTextAreaElement).value;
    // ① Format jobops://<job-title> (no special chars, no spaces, lowercase)
    let jobTitle = (data.title || "untitled").toLowerCase().replace(/[^a-z0-9]/g, "");
    const prefix = `jobops://${jobTitle}`;
    const clipboardContent = `${prefix}\n\n${data.body || ""}`;
    // ② Copy to clipboard
    try {
      await navigator.clipboard.writeText(clipboardContent);
      (document.getElementById("clip-status") as HTMLElement).textContent = "Copied to clipboard!";
      setTimeout(() => window.close(), 1200);
    } catch (e) {
      (document.getElementById("clip-status") as HTMLElement).textContent = "Failed to copy to clipboard.";
    }
  };

  (document.getElementById("cancel") as HTMLButtonElement).onclick = () => window.close();
});
