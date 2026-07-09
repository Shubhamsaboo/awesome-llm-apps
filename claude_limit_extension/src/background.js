// MV3 service worker. Runs periodic refreshes via chrome.alarms, keeps the
// toolbar badge up to date, and answers "refresh now" messages from popup/options.

import { browserApi } from "./lib/browser-polyfill.js";
import { fetchSnapshot, ApiError } from "./lib/api.js";
import { loadSnapshot, saveSnapshot, loadSettings, onSettingsChanged } from "./lib/storage.js";
import { badgePercent, accentFor } from "./lib/format.js";

const ALARM_NAME = "limitwatch.refresh";
const MIN_INTERVAL = 1;
const MAX_INTERVAL = 60;

// ---------------- lifecycle ----------------

browserApi.runtime.onInstalled.addListener(async () => {
  await ensureAlarm();
  await refreshCycle("install");
});

browserApi.runtime.onStartup.addListener(async () => {
  await ensureAlarm();
  await refreshCycle("startup");
});

browserApi.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === ALARM_NAME) await refreshCycle("alarm");
});

onSettingsChanged(async (settings) => {
  await ensureAlarm(settings);
  await paintBadge(await loadSnapshot(), settings);
});

// ---------------- messages from popup/options ----------------

browserApi.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "REFRESH_NOW") {
    (async () => {
      try {
        const snapshot = await refreshCycle("manual");
        sendResponse({ ok: true, snapshot });
      } catch (err) {
        sendResponse({ ok: false, error: serialize(err) });
      }
    })();
    return true; // keep the channel open for async sendResponse
  }
  if (msg?.type === "GET_LAST_SNAPSHOT") {
    (async () => sendResponse({ snapshot: await loadSnapshot() }))();
    return true;
  }
  return false;
});

// ---------------- core ----------------

async function ensureAlarm(settings) {
  const s = settings ?? (await loadSettings());
  const minutes = clamp(s.refreshIntervalMinutes, MIN_INTERVAL, MAX_INTERVAL);
  await browserApi.alarms.clear(ALARM_NAME);
  await browserApi.alarms.create(ALARM_NAME, {
    delayInMinutes: minutes,
    periodInMinutes: minutes,
  });
}

async function refreshCycle(_reason) {
  const settings = await loadSettings();
  try {
    const snapshot = await fetchSnapshot();
    await saveSnapshot(snapshot);
    await paintBadge(snapshot, settings);
    return snapshot;
  } catch (err) {
    await paintBadgeForError(err, settings);
    throw err;
  }
}

async function paintBadge(snapshot, settings) {
  if (!settings.showBadge || !snapshot) {
    await setBadge("", "#00000000");
    return;
  }
  const pct = badgePercent(snapshot.usage, settings.badgeSource);
  if (pct == null) {
    await setBadge("", "#00000000");
    return;
  }
  await setBadge(`${Math.round(pct)}`, accentFor(pct));
}

async function paintBadgeForError(err, settings) {
  if (!settings.showBadge) return;
  if (err instanceof ApiError && err.kind === "LOGGED_OUT") {
    await setBadge("!", "#9A928A");
  } else {
    await setBadge("!", "#C24040");
  }
}

async function setBadge(text, color) {
  await browserApi.action.setBadgeText({ text });
  await browserApi.action.setBadgeBackgroundColor({ color });
  if (browserApi.action.setBadgeTextColor) {
    // Chrome exposes this; Firefox picks contrast automatically.
    await browserApi.action.setBadgeTextColor({ color: "#FFFFFF" });
  }
}

function clamp(n, min, max) {
  if (typeof n !== "number" || Number.isNaN(n)) return 15;
  return Math.max(min, Math.min(max, Math.round(n)));
}

function serialize(err) {
  return {
    kind: err?.kind ?? "UNKNOWN",
    message: err?.message ?? String(err),
  };
}
