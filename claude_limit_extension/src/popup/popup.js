import { browserApi } from "../lib/browser-polyfill.js";
import { formatPercent, untilReset, sinceEpoch } from "../lib/format.js";

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

// ---------------- rendering (DOM API only, no innerHTML) ----------------

function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k === "style") {
      for (const [sk, sv] of Object.entries(v)) node.style[sk] = sv;
    } else if (k.startsWith("on") && typeof v === "function") {
      node.addEventListener(k.slice(2).toLowerCase(), v);
    } else {
      node.setAttribute(k, v);
    }
  }
  for (const c of children) {
    if (c == null || c === false) continue;
    node.append(c instanceof Node ? c : String(c));
  }
  return node;
}

function renderSkeleton() {
  $subtitle.textContent = "Loading…";
  $body.classList.add("skeleton");
  clear($body);
  $body.append(
    cardShell("Session · 5h"),
    cardShell("Weekly · 7d"),
    cardShell("Weekly · Opus"),
  );
}

function render(snapshot) {
  $body.classList.remove("skeleton");
  const usage = snapshot.usage;
  const account = snapshot.account;
  const subtitleParts = [];
  if (account?.email) subtitleParts.push(account.email);
  subtitleParts.push(`Updated ${sinceEpoch(snapshot.fetchedAtEpochMs)}`);
  $subtitle.textContent = subtitleParts.join(" · ");

  clear($body);
  $body.append(cardNode("Session · 5h", usage.five_hour));
  $body.append(cardNode("Weekly · 7d", usage.seven_day));
  if (usage.seven_day_opus) $body.append(cardNode("Weekly · Opus", usage.seven_day_opus));
  if (usage.seven_day_sonnet) $body.append(cardNode("Weekly · Sonnet", usage.seven_day_sonnet));
  if (usage.extra_usage?.is_enabled) $body.append(extraUsageCard(usage.extra_usage));
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
  clear($body);
  $body.append(
    el("div", { class: "state error" },
      el("div", { class: "k err", text: title }),
      el("div", { class: "v", text: explain }),
      el("button", {
        class: "btn",
        type: "button",
        text: btnLabel,
        onClick: async () => {
          if (isLoggedOut) {
            await browserApi.tabs.create({ url: "https://claude.ai/login" });
          } else {
            await refresh();
          }
        },
      }),
    ),
  );
}

function cardNode(label, window) {
  const percent = window?.utilization ?? null;
  const cls = severityClass(percent);
  const width = Math.max(0, Math.min(100, percent ?? 0)).toFixed(1);
  const resetText = window?.resets_at
    ? `Reset in ${untilReset(window.resets_at) ?? "—"}`
    : "";

  return el("div", { class: `card ${cls}` },
    el("div", { class: "card-head" },
      el("div", { class: "card-label", text: label }),
      el("div", { class: "card-value", text: formatPercent(percent) }),
    ),
    el("div", { class: "bar" },
      el("span", { style: { width: `${width}%` } }),
    ),
    resetText ? el("div", { class: "card-reset", text: resetText }) : null,
  );
}

function cardShell(label) {
  return el("div", { class: "card mist" },
    el("div", { class: "card-head" },
      el("div", { class: "card-label", text: label }),
      el("div", { class: "card-value", text: "—" }),
    ),
    el("div", { class: "bar" }, el("span", { style: { width: "0%" } })),
    el("div", { class: "card-reset", text: " " }),
  );
}

function extraUsageCard(extra) {
  const percent = extra.utilization ?? null;
  const cls = severityClass(percent);
  const width = Math.max(0, Math.min(100, percent ?? 0)).toFixed(1);
  const balance = extra.monthly_limit != null && extra.used_credits != null
    ? `$${extra.used_credits.toFixed(2)} / $${extra.monthly_limit.toFixed(2)}`
    : formatPercent(percent);

  return el("div", { class: `card ${cls}` },
    el("div", { class: "card-head" },
      el("div", { class: "card-label", text: "Extra usage" }),
      el("div", { class: "card-value", text: balance }),
    ),
    el("div", { class: "bar" }, el("span", { style: { width: `${width}%` } })),
  );
}

function severityClass(percent) {
  if (percent == null) return "mist";
  if (percent >= 90) return "red";
  if (percent >= 70) return "amber";
  return "orange";
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
