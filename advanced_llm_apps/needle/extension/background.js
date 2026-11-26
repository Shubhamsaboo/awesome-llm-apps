chrome.runtime.onInstalled.addListener(({ reason }) => {
  if (reason === "install") chrome.runtime.openOptionsPage();
});

chrome.action.onClicked.addListener(async (tab) => {
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["text-range.js", "content.js"],
    });
  } catch {
    await chrome.runtime.openOptionsPage();
  }
});
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "NEEDLE_SETTINGS") {
    chrome.runtime.openOptionsPage();
    return;
  }
  if (message.type !== "NEEDLE_SEARCH" || !sender.tab) return;
  (async () => {
    const { server = "http://127.0.0.1:4199", token = "" } =
      await chrome.storage.local.get(["server", "token"]);
    try {
      const response = await fetch(`${server}/api/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "x-needle-token": token } : {}),
        },
        body: JSON.stringify(message.payload),
        signal: AbortSignal.timeout(55000),
      });
      const data = await response.json();
      sendResponse(
        response.ok
          ? data
          : {
              error: data.error || "Search failed. Check your server settings.",
            },
      );
    } catch {
      sendResponse({
        error:
          "Cannot reach Needle. Start the server or check extension settings.",
      });
    }
  })();
  return true;
});
