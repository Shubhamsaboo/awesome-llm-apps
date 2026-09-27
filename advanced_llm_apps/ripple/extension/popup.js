(async () => {
  const status = document.getElementById("status"),
    button = document.getElementById("enable");
  let tab;
  try {
    const health = await chrome.runtime.sendMessage({ type: "health" });
    if (!health?.ok || !health.ready) {
      status.dataset.state = "error";
      status.textContent =
        health?.error ||
        "Start the local Ripple service with your TypeSafe API key.";
      return;
    }
    [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (
      !/^https:\/\/docs\.google\.com\/document\/d\/[^/]+\/edit/.test(
        tab?.url || "",
      )
    ) {
      status.textContent = "Open a Google Doc in this browser first.";
      return;
    }
    status.dataset.state = health.suggestionsReady ? "ready" : "pending";
    status.textContent = health.suggestionsReady
      ? "Jev + Gemini connected."
      : "Jev connected. Add a Gemini key for suggestions.";
    button.disabled = false;
    button.onclick = async () => {
      try {
        await chrome.tabs.sendMessage(tab.id, {
          type: "toggle",
          enabled: true,
        });
        window.close();
      } catch {
        status.textContent = "Reload this Google Doc once, then enable Ripple.";
      }
    };
  } catch {
    status.dataset.state = "error";
    status.textContent = "Reload the extension and try again.";
  }
})();
