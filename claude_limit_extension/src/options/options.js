import { loadSettings, saveSettings } from "../lib/storage.js";

const $interval = document.getElementById("interval");
const $intervalValue = document.getElementById("intervalValue");
const $showBadge = document.getElementById("showBadge");
const $badgeSource = document.getElementById("badgeSource");
const $saved = document.getElementById("saved");

let savedTimer = null;

init();

async function init() {
  const s = await loadSettings();
  $interval.value = String(s.refreshIntervalMinutes);
  $intervalValue.textContent = `${s.refreshIntervalMinutes} min`;
  $showBadge.checked = !!s.showBadge;
  $badgeSource.value = s.badgeSource;

  $interval.addEventListener("input", () => {
    $intervalValue.textContent = `${$interval.value} min`;
  });
  $interval.addEventListener("change", persist);
  $showBadge.addEventListener("change", persist);
  $badgeSource.addEventListener("change", persist);
}

async function persist() {
  await saveSettings({
    refreshIntervalMinutes: Number($interval.value),
    showBadge: $showBadge.checked,
    badgeSource: $badgeSource.value,
  });
  flashSaved();
}

function flashSaved() {
  $saved.hidden = false;
  clearTimeout(savedTimer);
  savedTimer = setTimeout(() => { $saved.hidden = true; }, 1200);
}
