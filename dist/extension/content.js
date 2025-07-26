"use strict";
(() => {
  // src/content.ts
  console.log("[JobOps Clipper] Content script loaded");
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    console.log("[JobOps Clipper] Received message:", msg);
    if (msg.action === "clip_page") {
      try {
        const title = document.title || "";
        const url = window.location.href;
        let body = document.body?.innerText || "";
        if (!body) {
          body = document.body?.textContent || "";
        }
        const metaDescription = document.querySelector('meta[name="description"]')?.getAttribute("content") || "";
        const metaKeywords = document.querySelector('meta[name="keywords"]')?.getAttribute("content") || "";
        const ogTitle = document.querySelector('meta[property="og:title"]')?.getAttribute("content") || "";
        const ogDescription = document.querySelector('meta[property="og:description"]')?.getAttribute("content") || "";
        const ogImage = document.querySelector('meta[property="og:image"]')?.getAttribute("content") || "";
        const ogType = document.querySelector('meta[property="og:type"]')?.getAttribute("content") || "";
        const ogSiteName = document.querySelector('meta[property="og:site_name"]')?.getAttribute("content") || "";
        const canonical = document.querySelector('link[rel="canonical"]')?.getAttribute("href") || "";
        const headings = Array.from(document.querySelectorAll("h1, h2, h3")).map((h) => ({
          tag: h.tagName,
          text: h.textContent?.trim() || ""
        }));
        const images = Array.from(document.images).filter((img) => img.src && img.offsetParent !== null).map((img) => ({
          src: img.src,
          alt: img.alt || ""
        }));
        let selectedText = "";
        try {
          selectedText = window.getSelection()?.toString() || "";
        } catch {
        }
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
          created_at: (/* @__PURE__ */ new Date()).toISOString(),
          jobops_action: "generate"
        };
        const jobData = Object.fromEntries(
          Object.entries(jobDataRaw).filter(
            ([_, v]) => Array.isArray(v) ? v.length > 0 : v && String(v).trim() !== ""
          )
        );
        console.log("[JobOps Clipper] Extracted data:", {
          title: jobData.title,
          url: jobData.url,
          bodyLength: jobData.body ? jobData.body.length : 0,
          imagesCount: jobData.images ? jobData.images.length : 0,
          headingsCount: jobData.headings ? jobData.headings.length : 0
        });
        chrome.runtime.sendMessage({ action: "show_preview", jobData });
        sendResponse({ jobData });
      } catch (e) {
        console.error("[JobOps Clipper] Error extracting content:", e);
        sendResponse({ error: "Exception during extraction: " + (e instanceof Error ? e.message : String(e)) });
      } finally {
        console.log("[JobOps Clipper] Content script unloaded");
      }
    }
    return true;
  });
})();
