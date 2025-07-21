/// <reference types="chrome" />

console.log("[JobOps Clipper] Content script loaded");

chrome.runtime.onMessage.addListener((msg: { action: string }, sender: chrome.runtime.MessageSender, sendResponse: (response?: any) => void) => {
  console.log("[JobOps Clipper] Received message:", msg);
  if (msg.action === "clip_page") {
    try {
      const title = document.title;
      const url = window.location.href;
      // Extract visible text as a placeholder for markdown
      const body = document.body.innerText;
      if (!title || !body) {
        console.warn("[JobOps Clipper] No title or body extracted.");
        sendResponse({ error: "No content extracted" });
        return;
      }
      console.log("[JobOps Clipper] Extracted content:", { title, url, bodyLength: body.length });
      sendResponse({ title, url, body });
    } catch (e) {
      console.error("[JobOps Clipper] Error extracting content:", e);
      sendResponse({ error: "Exception during extraction: " + (e instanceof Error ? e.message : String(e)) });
    } finally {
      console.log("[JobOps Clipper] Content script unloaded");
    }
  }
  // Return true to indicate async response if needed
  return true;
}); 