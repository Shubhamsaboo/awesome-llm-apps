const API = "http://127.0.0.1:4212";
const allowed = (sender) =>
  sender.id === chrome.runtime.id &&
  (sender.url?.startsWith(chrome.runtime.getURL("")) ||
    /^https:\/\/docs\.google\.com\/document\/d\/[^/]+\/edit/.test(
      sender.url || "",
    ));
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (
    !allowed(sender) ||
    !["health", "check", "suggest"].includes(message?.type)
  )
    return;
  (async () => {
    try {
      let response;
      for (let attempt = 0; attempt < 3; attempt++) {
        response = await fetch(
          API +
            (message.type === "health"
              ? "/health"
              : message.type === "suggest"
                ? "/suggest"
                : "/check"),
          {
            method: message.type === "health" ? "GET" : "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Ripple-Client": chrome.runtime.id,
            },
            ...(message.type !== "health"
              ? { body: JSON.stringify(message.input) }
              : {}),
            signal: AbortSignal.timeout(85000),
          },
        );
        if (response.status !== 429) break;
        await new Promise((resolve) =>
          setTimeout(resolve, 1500 * (attempt + 1)),
        );
      }
      const data = await response.json();
      if (!response.ok) {
        respond({
          ok: false,
          error: data.error || "The check failed.",
          retryable: response.status === 429 && data.retryable === true,
        });
        return;
      }
      respond({ ok: true, ...data });
    } catch (error) {
      respond({
        ok: false,
        error:
          error.message === "Failed to fetch"
            ? "Start the Ripple service on this computer, then retry."
            : error.message,
      });
    }
  })();
  return true;
});
