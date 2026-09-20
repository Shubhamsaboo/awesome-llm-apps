const form = document.querySelector("#settings"),
  server = document.querySelector("#server"),
  token = document.querySelector("#token"),
  status = document.querySelector("#status");
chrome.storage.local.get(["server", "token"]).then((data) => {
  server.value = data.server || "http://127.0.0.1:4199";
  token.value = data.token || "";
});
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const url = new URL(server.value);
    if (
      !["http:", "https:"].includes(url.protocol) ||
      url.username ||
      url.password
    )
      throw new Error("Enter an http or https server URL.");
    if (
      url.protocol !== "https:" &&
      !["localhost", "127.0.0.1"].includes(url.hostname)
    )
      throw new Error("Use HTTPS for a remote server.");
    const granted = await chrome.permissions.request({
      origins: [`${url.protocol}//${url.hostname}/*`],
    });
    if (!granted) throw new Error("Permission is needed to reach this server.");
    await chrome.storage.local.set({
      server: url.origin,
      token: token.value.trim(),
    });
    status.textContent = "Saved. Open a webpage and click the Needle icon.";
  } catch (error) {
    status.textContent = error.message;
  }
});
