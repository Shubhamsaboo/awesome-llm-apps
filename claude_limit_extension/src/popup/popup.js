import { browserApi } from "../lib/browser-polyfill.js";
import { formatPercent, accentFor, untilReset, sinceEpoch } from "../lib/format.js";

const $body = document.getElementById("body");
const $subtitle = document.getElementById("subtitle");
const $refresh = document.getElementById("refresh");
const $openClaude = document.getElementById("openClaude");
const $openOptions = document.getElementById("openOptions");

$refresh.addEventListener("click", () => refresh());
$openClaude.addEventListener("click", async () => {
  await browserApi.tabs.create({ url: "https://claude.ai" });
});
$openOptions.addEventListener("click", async () => {
  if (browserApi.runtime.openOptionsPage) {
    await browserApi.runtime.openOptionsPage();
  } else {
    await browserApi.tabs.create({ url: browserApi.runtime.getURL("src/options/options.html") });
  }
});

// on open: show cached snapshot immediately, then refresh in the background
init().catch((e) => console.error("[popup] init failed", e));

async function init() {
  const cached = await getCachedSnapshot();
  if (cached) render(cached);
  else renderSkeleton();
  await refresh();
}

async function refresh() {
  $refresh.classList.add("spin");
  const response = await sendMessage({ type: "REFRESH_NOW" });
  $refresh.classList.remove("spin");
  if (response?.ok) {
    render(response.snapshot);
  } else {
    renderError(response?.error ?? { kind: "UNKNOWN", message: "Unknown error" });
  }
}

function renderSkeleton() {
  $subtitle.textContent = "Loading…";
  $body.classList.add("skeleton");
  $body.innerHTML = `
    ${cardShell("Session · 5h")}
    ${cardShell("Weekly · 7d")}
    ${cardShell("Weekly · Opus")}
  `;
}

function render(snapshot) {
  $body.classList.remove("skeleton");
  const usage = snapshot.usage;
  const account = snapshot.account;
  const subtitleParts = [];
  if (account?.email) subtitleParts.push(account.email);
  subtitleParts.push(`Updated ${sinceEpoch(snapshot.fetchedAtEpochMs)}`);
  $subtitle.textContent = subtitleParts.join(" · ");

  const cards = [];
  cards.push(cardHtml("Session · 5h", usage.five_hour));
  cards.push(cardHtml("Weekly · 7d", usage.seven_day));
  if (usage.seven_day_opus) cards.push(cardHtml("Weekly · Opus", usage.seven_day_opus));
  if (usage.seven_day_sonnet) cards.push(cardHtml("Weekly · Sonnet", usage.seven_day_sonnet));
  if (usage.extra_usage?.is_enabled) cards.push(extraUsageCard(usage.extra_usage));

  $body.innerHTML = cards.join("\n");
}

function renderError(err) {
  $body.classList.remove("skeleton");
  const isLoggedOut = err.kind === "LOGGED_OUT";
  const isNetwork = err.kind === "NETWORK";

  const title = isLoggedOut
    ? "Not signed in to claude.ai"
    : isNetwork
      ? "Network error"
      : "Couldn't fetch usage";

  const explain = isLoggedOut
    ? "Open claude.ai and sign in. The extension reads limits from your existing browser session."
    : err.message;

  const btnLabel = isLoggedOut ? "Open claude.ai" : "Retry";

  $subtitle.textContent = "Error";
  $body.innerHTML = `
    <div class="state error">
      <div class="k err">${escapeHtml(title)}</div>
      <div class="v">${escapeHtml(explain)}</div>
      <button class="btn" id="stateAction" type="button">${btnLabel}</button>
    </div>
  `;
  const action = document.getElementById("stateAction");
  action?.addEventListener("click", async () => {
    if (isLoggedOut) {
      await browserApi.tabs.create({ url: "https://claude.ai/login" });
    } else {
      await refresh();
    }
  });
}

function cardHtml(label, window) {
  const percent = window?.utilization ?? null;
  const cls = severityClass(percent);
  const width = Math.max(0, Math.min(100, percent ?? 0)).toFixed(1);
  const reset = window?.resets_at ? `Reset in ${escapeHtml(untilReset(window.resets_at) ?? "—")}` : "";
  return `
    <div class="card ${cls}">
      <div class="card-head">
        <div class="card-label">${escapeHtml(label)}</div>
        <div class="card-value">${escapeHtml(formatPercent(percent))}</div>
      </div>
      <div class="bar"><span style="width:${width}%"></span></div>
      ${reset ? `<div class="card-reset">${reset}</div>` : ""}
    </div>
  `;
}

function cardShell(label) {
  return `
    <div class="card mist">
      <div class="card-head">
        <div class="card-label">${escapeHtml(label)}</div>
        <div class="card-value">—</div>
      </div>
      <div class="bar"><span style="width:0%"></span></div>
      <div class="card-reset">&nbsp;</div>
    </div>
  `;
}

function extraUsageCard(extra) {
  const percent = extra.utilization ?? null;
  const cls = severityClass(percent);
  const width = Math.max(0, Math.min(100, percent ?? 0)).toFixed(1);
  const balance = extra.monthly_limit != null && extra.used_credits != null
    ? `$${extra.used_credits.toFixed(2)} / $${extra.monthly_limit.toFixed(2)}`
    : "";
  return `
    <div class="card ${cls}">
      <div class="card-head">
        <div class="card-label">Extra usage</div>
        <div class="card-value">${escapeHtml(balance || formatPercent(percent))}</div>
      </div>
      <div class="bar"><span style="width:${width}%"></span></div>
    </div>
  `;
}

function severityClass(percent) {
  if (percent == null) return "mist";
  if (percent >= 90) return "red";
  if (percent >= 70) return "amber";
  return "orange";
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]
  ));
}

async function getCachedSnapshot() {
  const res = await sendMessage({ type: "GET_LAST_SNAPSHOT" });
  return res?.snapshot ?? null;
}

function sendMessage(msg) {
  // Chrome 99+ and Firefox both return a Promise from sendMessage(msg) with no
  // callback. We swallow the "no receiver" rejection so a torn-down worker
  // doesn't blow up the popup.
  const result = browserApi.runtime.sendMessage(msg);
  return Promise.resolve(result).catch(() => null);
}
