// Tiny cross-browser shim. In Firefox `browser.*` is native and returns promises;
// in Chrome we alias `chrome.*` to `browser` and rely on MV3 chrome.* returning
// promises for the surfaces we use (storage, alarms, tabs, action).
export const browserApi = (() => {
  if (typeof globalThis.browser !== "undefined" && globalThis.browser.storage) {
    return globalThis.browser;
  }
  return globalThis.chrome;
})();
