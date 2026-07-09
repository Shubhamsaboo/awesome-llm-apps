// Thin wrapper over browser.storage.local so callers don't touch the raw API.
import { browserApi } from "./browser-polyfill.js";

const KEY_SNAPSHOT = "snapshot";
const KEY_SETTINGS = "settings";

const DEFAULT_SETTINGS = {
  refreshIntervalMinutes: 15, // 1..60
  showBadge: true,
  badgeSource: "highest", // "highest" | "session" | "weekly"
};

export async function loadSnapshot() {
  const out = await browserApi.storage.local.get(KEY_SNAPSHOT);
  return out[KEY_SNAPSHOT] ?? null;
}

export async function saveSnapshot(snapshot) {
  await browserApi.storage.local.set({ [KEY_SNAPSHOT]: snapshot });
}

export async function loadSettings() {
  const out = await browserApi.storage.local.get(KEY_SETTINGS);
  return { ...DEFAULT_SETTINGS, ...(out[KEY_SETTINGS] ?? {}) };
}

export async function saveSettings(partial) {
  const merged = { ...(await loadSettings()), ...partial };
  await browserApi.storage.local.set({ [KEY_SETTINGS]: merged });
  return merged;
}

export function onSettingsChanged(callback) {
  browserApi.storage.onChanged.addListener((changes, area) => {
    if (area !== "local") return;
    if (changes[KEY_SETTINGS]) callback(changes[KEY_SETTINGS].newValue ?? DEFAULT_SETTINGS);
  });
}
