const SIGNALS = {
  numbers_reconciler: {
    label: "Financial metric",
    shortLabel: "Metric",
    color: "#ffad9b",
    threshold: "Numbers that change the investment picture",
  },
  cfo_tone: {
    label: "Tone shift",
    shortLabel: "Tone",
    color: "#8cf5c2",
    threshold: "Confidence, caution, hedging, or defensiveness",
  },
  peer_context: {
    label: "Peer context",
    shortLabel: "Peers",
    color: "#6f96ff",
    threshold: "Company-specific versus sector-wide read-through",
  },
  surprise_detector: {
    label: "Surprise",
    shortLabel: "Surprise",
    color: "#ff7759",
    threshold: "New, contradictory, or market-moving statements",
  },
  filing_grounder: {
    label: "Filing check",
    shortLabel: "Filings",
    color: "#d9d9dd",
    threshold: "Transcript claim tied back to filings",
  },
  market_narrator: {
    label: "Context",
    shortLabel: "Context",
    color: "#93939f",
    threshold: "Source validation or call-level framing",
  },
};

let player = null;
let playerApiReady = false;
let activeSessionId = "";
let sessionData = null;
let pollTimer = null;
let playbackTimer = null;
const revealed = new Set();

const form = document.getElementById("urlForm");
const input = document.getElementById("youtubeUrl");
const analyzeButton = document.getElementById("analyzeButton");
const healthLine = document.getElementById("healthLine");
const statusText = document.getElementById("statusText");
const progressBar = document.getElementById("progressBar");
const statusSteps = Array.from(document.querySelectorAll(".status-steps span"));
const companyBadge = document.getElementById("companyBadge");
const researchGrid = document.getElementById("researchGrid");
const timecode = document.getElementById("timecode");
const watchState = document.getElementById("watchState");
const timelineFeed = document.getElementById("timelineFeed");
const timelineStatus = document.getElementById("timelineStatus");
const streamSummary = document.getElementById("streamSummary");
const revealNextButton = document.getElementById("revealNextButton");
const showAllButton = document.getElementById("showAllButton");
const videoPanel = document.querySelector(".video-panel");

window.onYouTubeIframeAPIReady = () => {
  playerApiReady = true;
};
if (window.YT && window.YT.Player) {
  playerApiReady = true;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const youtubeUrl = input.value.trim();
  if (!youtubeUrl) return;

  resetWorkspace();
  analyzeButton.disabled = true;
  setStatus(4, "Creating analysis session");

  try {
    const response = await fetch("/api/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ youtube_url: youtubeUrl }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Could not create session.");
    }
    const payload = await response.json();
    activeSessionId = payload.session_id;
    pollSession();
    pollTimer = window.setInterval(pollSession, 1500);
  } catch (error) {
    analyzeButton.disabled = false;
    setStatus(100, error.message);
  }
});

revealNextButton.addEventListener("click", () => revealNextInsight());
showAllButton.addEventListener("click", () => revealAllInsights());

async function pollSession() {
  if (!activeSessionId) return;
  let payload;
  try {
    const response = await fetch(`/api/sessions/${activeSessionId}`);
    if (!response.ok) throw new Error("Backend session lookup failed.");
    payload = await response.json();
  } catch (error) {
    setStatus(100, error.message || "Backend connection dropped.");
    window.clearInterval(pollTimer);
    analyzeButton.disabled = false;
    return;
  }
  setStatus(payload.progress || 0, payload.message || payload.status);

  if (payload.status === "error") {
    window.clearInterval(pollTimer);
    analyzeButton.disabled = false;
    setStatus(100, payload.error || "Analysis failed.");
    return;
  }

  if (payload.data) {
    sessionData = payload.data;
    renderSession(sessionData);
  }

  if (payload.status === "ready") {
    window.clearInterval(pollTimer);
    analyzeButton.disabled = false;
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/health");
    const health = await response.json();
    healthLine.textContent = health.has_google_key
      ? "Gemini key detected"
      : "No Gemini key detected; local fallback available";
  } catch {
    healthLine.textContent = "Backend unavailable";
  }
}

function renderSession(data) {
  const videoId = data.video.video_id;
  if (!player) {
    mountPlayer(videoId);
  } else if (player.getVideoData && player.getVideoData().video_id !== videoId) {
    player.loadVideoById(videoId);
  }

  renderResearch(data.research);
  renderInsightDesk(data);
  renderAnalystTimeline(data.insights);
  watchState.textContent = data.insights.length
    ? "Analyst cards are synced to playback"
    : "Research loaded; no high-signal cards found";

  if (!playbackTimer) {
    playbackTimer = window.setInterval(syncPlayback, 500);
  }
}

function renderInsightDesk(data) {
  const total = data.insights.length;
  const locked = Math.max(0, total - revealed.size);
  if (total) {
    streamSummary.textContent = `${revealed.size} of ${total} analyst signals visible. Future signals stay collapsed until playback reaches them.`;
  } else {
    streamSummary.textContent = "The transcript and research loaded, but no strong investor signal was detected.";
  }
  revealNextButton.disabled = locked === 0;
  showAllButton.disabled = locked === 0;
}

function mountPlayer(videoId) {
  const mount = () => {
    player = new YT.Player("player", {
      videoId,
      playerVars: {
        rel: 0,
        modestbranding: 1,
        playsinline: 1,
      },
      events: {
        onReady: syncPlayback,
      },
    });
  };

  if (playerApiReady && window.YT && window.YT.Player) {
    mount();
  } else {
    const wait = window.setInterval(() => {
      if (playerApiReady && window.YT && window.YT.Player) {
        window.clearInterval(wait);
        mount();
      }
    }, 120);
  }
}

function renderResearch(research) {
  companyBadge.textContent = research.ticker
    ? `${research.company} · ${research.ticker}`
    : research.company;

  const docs = research.documents || [];
  const news = research.news || [];

  const peerText = research.peers && research.peers.length
    ? research.peers.map((peer) => `<span>${escapeHtml(peer)}</span>`).join("")
    : "<em>Unresolved</em>";

  const newsCard = news.length
    ? `
      <article class="research-card research-news">
        <span>News</span>
        <strong>Latest external context</strong>
        ${renderResearchLinks(news.slice(0, 4), "")}
      </article>
    `
    : "";

  researchGrid.innerHTML = `
    <article class="research-card research-primary">
      <span>Company</span>
      <strong>${escapeHtml(research.ticker || research.company)}</strong>
      <p>${escapeHtml(research.fiscal_period || "Period unresolved")}</p>
      <div class="research-chips">${peerText}</div>
    </article>
    <article class="research-card">
      <span>Filings</span>
      <strong>${docs.length ? "Primary source links" : "No SEC filing linked"}</strong>
      ${renderResearchLinks(docs.slice(0, 3), "Agent will cite transcript-first.")}
    </article>
    ${newsCard}
  `;
}

function syncPlayback() {
  if (!sessionData || !player || typeof player.getCurrentTime !== "function") return;
  const current = player.getCurrentTime();
  timecode.textContent = formatTime(current);
  revealDueInsights(current);
  updateTimelinePlayback(current);
}

function revealDueInsights(currentTime) {
  const due = sessionData.insights
    .filter((insight) => insight.start_time <= currentTime && !revealed.has(insight.id))
    .sort((a, b) => a.start_time - b.start_time);

  if (!due.length) return;
  due.forEach((insight) => revealed.add(insight.id));
  updateRevealState({ scrollToId: due[due.length - 1].id });
}

function revealNextInsight() {
  if (!sessionData) return;
  const next = sessionData.insights.find((insight) => !revealed.has(insight.id));
  if (next) {
    revealed.add(next.id);
    seekTo(next.start_time, { reveal: false });
    updateRevealState({ scrollToId: next.id });
  }
}

function revealAllInsights() {
  if (!sessionData) return;
  sessionData.insights.forEach((insight) => revealed.add(insight.id));
  updateRevealState();
}

function revealInsightById(id) {
  if (!sessionData || !id) return;
  const insight = sessionData.insights.find((item) => item.id === id);
  if (!insight) return;
  revealed.add(insight.id);
  seekTo(insight.start_time, { reveal: false });
  updateRevealState({ scrollToId: insight.id });
}

function updateRevealState(options = {}) {
  if (sessionData) {
    renderInsightDesk(sessionData);
    renderAnalystTimeline(sessionData.insights);
    if (options.scrollToId) scrollTimelineTo(options.scrollToId);
  }
}

function renderAnalystTimeline(insights) {
  if (!insights.length) {
    timelineStatus.textContent = "Quiet";
    timelineFeed.innerHTML = '<div class="empty-feed">No high-signal analyst cards were emitted for this source.</div>';
    return;
  }

  const current = getCurrentPlaybackTime();
  const next = insights.find((insight) => !revealed.has(insight.id));
  timelineStatus.textContent = next ? `Next ${formatTime(next.start_time)}` : "All visible";
  timelineFeed.innerHTML = insights.map((insight) => renderTimelineItem(insight, current)).join("");
  timelineFeed.querySelectorAll("[data-action='jump']").forEach((button) => {
    button.addEventListener("click", () => {
      revealInsightById(button.dataset.id);
    });
  });
}

function renderTimelineItem(insight, current) {
  const meta = SIGNALS[insight.agent] || SIGNALS.market_narrator;
  const state = revealed.has(insight.id)
    ? "revealed"
    : current >= insight.start_time
      ? "current"
      : "upcoming";
  const stateLabel = state === "revealed" ? "Seen" : state === "current" ? "Now" : "Upcoming";
  if (state === "upcoming") {
    return `
      <article class="timeline-card upcoming" style="--agent-color: ${meta.color}" data-id="${escapeHtml(insight.id)}">
        <div class="time-rail">
          <span>${formatTime(insight.start_time)}</span>
        </div>
        <div class="card-body">
          <div class="card-top">
            <span class="agent-tag">${escapeHtml(meta.label)}</span>
            <span class="severity">${stateLabel}</span>
          </div>
          <h3>Signal queued</h3>
          <p class="quote preview">${escapeHtml(meta.threshold)}</p>
          <div class="card-foot">
            <button type="button" data-action="jump" data-id="${escapeHtml(insight.id)}">Jump and reveal</button>
            <div class="citations">Unlocks at ${formatTime(insight.start_time)}</div>
          </div>
        </div>
      </article>
    `;
  }
  return `
    <article class="timeline-card ${state}" style="--agent-color: ${meta.color}" data-id="${escapeHtml(insight.id)}">
      <div class="time-rail">
        <span>${formatTime(insight.start_time)}</span>
      </div>
      <div class="card-body">
        <div class="card-top">
          <span class="agent-tag">${escapeHtml(meta.label)}</span>
          <span class="severity">${stateLabel}</span>
        </div>
        <h3>${escapeHtml(insight.headline)}</h3>
        <p class="quote">${escapeHtml(stripOuterQuotes(insight.quote))}</p>
        ${insight.explanation ? `<p class="why">${escapeHtml(insight.explanation)}</p>` : ""}
        ${renderMiniViz(insight.mini_viz)}
        <div class="card-foot">
          <button type="button" data-action="jump" data-id="${escapeHtml(insight.id)}">Jump to quote</button>
          <div class="citations">${renderCitations(insight.citations)}</div>
        </div>
      </div>
    </article>
  `;
}

function updateTimelinePlayback(current) {
  if (!sessionData || !timelineFeed) return;
  timelineFeed.querySelectorAll(".timeline-card").forEach((card) => {
    const insight = sessionData.insights.find((item) => item.id === card.dataset.id);
    if (!insight) return;
    const state = revealed.has(insight.id)
      ? "revealed"
      : current >= insight.start_time
        ? "current"
        : "upcoming";
    card.classList.toggle("revealed", state === "revealed");
    card.classList.toggle("current", state === "current");
    card.classList.toggle("upcoming", state === "upcoming");
  });
}

function scrollTimelineTo(id) {
  const card = timelineFeed.querySelector(`[data-id="${CSS.escape(id)}"]`);
  if (!card) return;
  card.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function getCurrentPlaybackTime() {
  if (player && typeof player.getCurrentTime === "function") {
    try {
      return player.getCurrentTime();
    } catch {
      return 0;
    }
  }
  return 0;
}

function renderMiniViz(viz) {
  if (!viz) return "";
  const title = viz.title || viz.type || "Signal";
  if (viz.points && viz.points.length > 1) {
    return renderPointViz(viz, title);
  }
  const rows = (viz.rows || [])
    .filter((row) => row && (String(row[0] || "").trim() || String(row[1] || "").trim()))
    .slice(0, 5)
    .map((row) => `<div class="viz-row"><span>${escapeHtml(row[0] || "")}</span><strong>${escapeHtml(row[1] || "")}</strong></div>`)
    .join("");
  if (!rows) return "";
  return `<div class="mini-viz"><div class="viz-title">${escapeHtml(title)}</div>${rows}</div>`;
}

function renderPointViz(viz, title) {
  const rawPoints = (viz.points || [])
    .map((point) => Number(point))
    .filter((point) => Number.isFinite(point));
  if (rawPoints.length < 2) return "";

  const points = rawPoints.slice(-10);
  const sourceLabels = Array.isArray(viz.labels) ? viz.labels.slice(-10) : [];
  const labels = points.map((_, index) => {
    const label = sourceLabels[index];
    return label && String(label).trim() ? String(label).trim() : `Point ${index + 1}`;
  });
  const min = Math.min(...points);
  const max = Math.max(...points);
  const spread = max - min || 1;
  const latest = points[points.length - 1];
  const previous = points[points.length - 2];
  const change = latest - previous;
  const coordinates = points.map((point, index) => {
    const x = points.length === 1 ? 50 : 6 + (index / (points.length - 1)) * 88;
    const y = 40 - ((point - min) / spread) * 30;
    return { x, y, point, label: labels[index] };
  });
  const line = coordinates.map((point) => `${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(" ");
  const pointButtons = coordinates
    .map((coord) => {
      const tooltip = `${coord.label}: ${formatVizNumber(coord.point)}`;
      return `
        <button
          type="button"
          class="chart-point"
          style="left: ${coord.x}%; top: ${(coord.y / 46) * 100}%"
          title="${escapeHtml(tooltip)}"
          aria-label="${escapeHtml(tooltip)}"
          data-tooltip="${escapeHtml(tooltip)}"
        ></button>
      `;
    })
    .join("");
  const axisLabels = [coordinates[0], coordinates[coordinates.length - 1]]
    .filter(Boolean)
    .map((coord) => `<span style="left: ${coord.x}%">${escapeHtml(coord.label)}</span>`)
    .join("");

  return `
    <div class="mini-viz metric-viz">
      <div class="viz-title">${escapeHtml(title)}</div>
      <div class="viz-summary">
        <span><b>Latest</b>${formatVizNumber(latest)}</span>
        <span><b>Change</b>${change >= 0 ? "+" : ""}${formatVizNumber(change)}</span>
        <span><b>Range</b>${formatVizNumber(min)} - ${formatVizNumber(max)}</span>
      </div>
      <div class="metric-chart" role="img" aria-label="${escapeHtml(title)} values from ${escapeHtml(labels[0])} to ${escapeHtml(labels[labels.length - 1])}">
        <svg viewBox="0 0 100 46" preserveAspectRatio="none" aria-hidden="true">
          <line x1="0" y1="10" x2="100" y2="10"></line>
          <line x1="0" y1="25" x2="100" y2="25"></line>
          <line x1="0" y1="40" x2="100" y2="40"></line>
          <polyline points="${line}"></polyline>
        </svg>
        ${pointButtons}
      </div>
      <div class="chart-axis">${axisLabels}</div>
    </div>
  `;
}

function renderCitations(citations) {
  if (!citations || !citations.length) return "Transcript anchored";
  return citations
    .slice(0, 2)
    .map((citation) => {
      const label = escapeHtml(citation.label || citation.source || "Source");
      return citation.url ? `<a href="${escapeHtml(citation.url)}" target="_blank" rel="noreferrer">${label}</a>` : label;
    })
    .join("<br>");
}

function renderResearchLinks(items, fallback) {
  if (!items || !items.length) return `<p>${escapeHtml(fallback)}</p>`;
  return `
    <div class="research-links">
      ${items
        .map((item) => {
          const label = item.kind && item.kind !== "news" ? item.kind : item.title;
          return item.url
            ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>`
            : `<span>${escapeHtml(label)}</span>`;
        })
        .join("")}
    </div>
  `;
}

function seekTo(seconds, options = { reveal: true }) {
  if (player && typeof player.seekTo === "function") {
    player.seekTo(seconds, true);
    player.playVideo();
  }
  if (options.reveal !== false) {
    revealDueInsights(seconds);
  }
  timecode.textContent = formatTime(seconds);
}

function resetWorkspace() {
  window.clearInterval(pollTimer);
  pollTimer = null;
  if (player && typeof player.destroy === "function") {
    player.destroy();
  }
  player = null;
  setPlayerPlaceholder("Analyzing", "Building research and high-signal analyst cards");
  sessionData = null;
  activeSessionId = "";
  revealed.clear();
  timelineFeed.innerHTML = '<div class="empty-feed">Timestamped analyst cards will appear here.</div>';
  researchGrid.innerHTML = "";
  companyBadge.textContent = "No company loaded";
  timelineStatus.textContent = "Waiting";
  streamSummary.textContent = "Paste a URL to build a playback-synced analyst overlay.";
  timecode.textContent = "00:00";
  watchState.textContent = "Preparing analysis";
  revealNextButton.disabled = true;
  showAllButton.disabled = true;
}

function setStatus(progress, text) {
  progressBar.style.width = `${Math.max(0, Math.min(100, progress))}%`;
  statusText.textContent = text;
  updateStage(progress);
}

function updateStage(progress) {
  const ordered = [
    ["metadata", 10],
    ["transcript", 25],
    ["research", 45],
    ["analysis", 70],
    ["ready", 100],
  ];
  const active = [...ordered].reverse().find(([, threshold]) => progress >= threshold)?.[0] || "";
  statusSteps.forEach((step) => {
    const stage = step.dataset.stage;
    const threshold = ordered.find(([name]) => name === stage)?.[1] || 0;
    step.classList.toggle("done", progress >= threshold);
    step.classList.toggle("active", stage === active && progress < 100);
  });
}

function setPlayerPlaceholder(label, headline) {
  if (!videoPanel) return;
  videoPanel.innerHTML = `
    <div id="player" class="player-empty">
      <div class="empty-state">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(headline)}</strong>
      </div>
    </div>
  `;
}

function formatTime(seconds) {
  const total = Math.max(0, Math.floor(seconds));
  const mins = Math.floor(total / 60);
  const secs = total % 60;
  const hours = Math.floor(mins / 60);
  if (hours) {
    return `${hours}:${String(mins % 60).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function stripOuterQuotes(value) {
  const text = String(value ?? "").trim();
  return text.replace(/^["'“”‘’]+|["'“”‘’]+$/g, "");
}

function formatVizNumber(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "";
  const abs = Math.abs(number);
  if (abs >= 1000) return number.toLocaleString(undefined, { maximumFractionDigits: 1 });
  if (abs >= 100) return number.toLocaleString(undefined, { maximumFractionDigits: 1 });
  if (abs >= 10) return number.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return number.toLocaleString(undefined, { maximumFractionDigits: 3 });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

checkHealth();
