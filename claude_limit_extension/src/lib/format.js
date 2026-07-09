// Small formatters used by popup, options, and the badge.

export function untilReset(isoString) {
  if (!isoString) return null;
  const t = Date.parse(isoString);
  if (Number.isNaN(t)) return null;
  const deltaMs = t - Date.now();
  if (deltaMs <= 0) return "now";
  return formatDurationMs(deltaMs);
}

export function sinceEpoch(epochMs) {
  if (!epochMs) return "never";
  const deltaMs = Date.now() - epochMs;
  if (deltaMs < 60_000) return "just now";
  if (deltaMs < 3_600_000) return `${Math.floor(deltaMs / 60_000)}m ago`;
  if (deltaMs < 86_400_000) return `${Math.floor(deltaMs / 3_600_000)}h ago`;
  return `${Math.floor(deltaMs / 86_400_000)}d ago`;
}

export function formatPercent(v) {
  if (v == null || Number.isNaN(v)) return "—";
  return `${Math.round(v)}%`;
}

export function accentFor(percent) {
  if (percent == null) return "#9A928A"; // mist
  if (percent >= 90) return "#C24040";   // red
  if (percent >= 70) return "#E0A050";   // amber
  return "#CC785C";                      // orange
}

function formatDurationMs(ms) {
  const totalMin = Math.floor(ms / 60_000);
  const totalSec = Math.floor(ms / 1_000);
  const days = Math.floor(totalMin / (60 * 24));
  const hours = Math.floor((totalMin % (60 * 24)) / 60);
  const mins = totalMin % 60;
  if (days > 0) return `${days}d ${hours}h`;
  if (totalMin >= 60) return `${hours}h ${mins}m`;
  if (totalMin >= 1) return `${mins}m`;
  return `${totalSec}s`;
}

/**
 * Picks the "worst" utilization for the toolbar badge.
 * @param {import("./api.js").UsageResponse} usage
 * @param {"highest"|"session"|"weekly"} source
 */
export function badgePercent(usage, source) {
  if (!usage) return null;
  const s = usage.five_hour?.utilization ?? null;
  const w = usage.seven_day?.utilization ?? null;
  const o = usage.seven_day_opus?.utilization ?? null;
  const so = usage.seven_day_sonnet?.utilization ?? null;
  const all = [s, w, o, so].filter((v) => v != null);
  if (all.length === 0) return null;
  switch (source) {
    case "session": return s;
    case "weekly": return Math.max(...[w, o, so].filter((v) => v != null));
    case "highest":
    default: return Math.max(...all);
  }
}
