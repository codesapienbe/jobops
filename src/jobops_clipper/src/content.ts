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
      if (!title || !body) {
        console.warn("[JobOps Clipper] No title or body extracted.");
        sendResponse({ error: "No content extracted" });
        return;
      }
      console.log("[JobOps Clipper] Extracted content:", { title, url, bodyLength: body.length, metaDescription, metaKeywords, ogTitle, ogDescription, ogImage, ogType, ogSiteName, canonical, headings, images, selectedText });
      sendResponse({
        title,
        url,
        body,
        metaDescription,
        metaKeywords,
        ogTitle,
        ogDescription,
        ogImage,
        ogType,
        ogSiteName,
        canonical,
        headings,
        images,
        selectedText
        // html // Uncomment if you want to include full HTML
      });
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