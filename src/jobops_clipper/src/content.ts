/// <reference types="chrome" />

chrome.runtime.onMessage.addListener((msg: { action: string }, sender: chrome.runtime.MessageSender, sendResponse: (response?: any) => void) => {
  if (msg.action === "clip_page") {
    const title = document.title;
    const url = window.location.href;
    // Extract visible text as a placeholder for markdown
    const body = document.body.innerText;
    sendResponse({ title, url, body });
  }
}); 