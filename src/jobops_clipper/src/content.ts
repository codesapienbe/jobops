/// <reference types="chrome" />

console.log("[JobOps Clipper] Content script loaded");

chrome.runtime.onMessage.addListener((msg: { action: string }, sender: chrome.runtime.MessageSender, sendResponse: (response?: any) => void) => {
  console.log("[JobOps Clipper] Received message:", msg);
  if (msg.action === "clip_page") {
    try {
      const title = document.title || "";
      const url = window.location.href;
      let body = document.body?.innerText || "";
      if (!body) {
        // Try textContent as a fallback
        body = document.body?.textContent || "";
      }
      // Meta tags
      const metaDescription = document.querySelector('meta[name="description"]')?.getAttribute('content') || "";
      const metaKeywords = document.querySelector('meta[name="keywords"]')?.getAttribute('content') || "";
      // OpenGraph
      const ogTitle = document.querySelector('meta[property="og:title"]')?.getAttribute('content') || "";
      const ogDescription = document.querySelector('meta[property="og:description"]')?.getAttribute('content') || "";
      const ogImage = document.querySelector('meta[property="og:image"]')?.getAttribute('content') || "";
      const ogType = document.querySelector('meta[property="og:type"]')?.getAttribute('content') || "";
      const ogSiteName = document.querySelector('meta[property="og:site_name"]')?.getAttribute('content') || "";
      // Canonical link
      const canonical = document.querySelector('link[rel="canonical"]')?.getAttribute('href') || "";
      // Headings
      const headings = Array.from(document.querySelectorAll('h1, h2, h3')).map(h => ({
        tag: h.tagName,
        text: h.textContent?.trim() || ""
      }));
      // Images
      const images = Array.from(document.images).filter(img => img.src && img.offsetParent !== null).map(img => ({
        src: img.src,
        alt: img.alt || ""
      }));
      // Selected text
      let selectedText = "";
      try {
        selectedText = window.getSelection()?.toString() || "";
      } catch {}
      // Full HTML (optional, for advanced use)
      // const html = document.documentElement.outerHTML;
      if (!title && !body) {
        console.warn("[JobOps Clipper] No title or body extracted.");
        sendResponse({ error: "No content extracted" });
        return;
      }
      if (!title || !body) {
        console.warn(`[JobOps Clipper] Only partial content extracted. Title: '${title}', Body length: ${body.length}`);
      }
      const jobDataRaw = {
        title,
        url,
        body,
        metaDescription,
        metaKeywords,
        ogType,
        ogSiteName,
        canonical,
        headings,
        images,
        selectedText,
        created_at: new Date().toISOString(),
        jobops_action: 'generate'
      };
      // Remove empty fields
      const jobData = Object.fromEntries(
        Object.entries(jobDataRaw).filter(([_, v]) =>
          Array.isArray(v) ? v.length > 0 : v && String(v).trim() !== ""
        )
      );
      // Only send jobData to popup for preview, do NOT copy to clipboard here
      chrome.runtime.sendMessage({ action: "show_preview", jobData });
      sendResponse({ jobData }); // <-- Add this line to respond directly to popup
      // Clipboard write removed from content script
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