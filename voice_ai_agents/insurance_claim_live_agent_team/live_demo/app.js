const transcriptEl = document.querySelector("#transcript");
const notesEl = document.querySelector("#notes");
const pinboardEl = document.querySelector("#pinboard");
const stampEl = document.querySelector("#stamp");
const penEl = document.querySelector("#pen");
const neededListEl = document.querySelector("#neededList");
const teamFeedEl = document.querySelector("#teamFeed");
const readinessEl = document.querySelector("#readiness");
const callStatus = document.querySelector("#callStatus");
const modelLabel = document.querySelector("#modelLabel");
const pageDate = document.querySelector("#pageDate");
const micButton = document.querySelector("#micButton");
const cameraButton = document.querySelector("#cameraButton");
const cameraStage = document.querySelector("#cameraStage");
const cameraPreview = document.querySelector("#cameraPreview");
const frameCanvas = document.querySelector("#frameCanvas");
const newIntakeButton = document.querySelector("#newIntakeButton");
const textForm = document.querySelector("#textForm");
const textInput = document.querySelector("#textInput");
const packetDialog = document.querySelector("#packetDialog");
const packetMarkdownEl = document.querySelector("#packetMarkdown");

const DEFAULT_API_ORIGIN = "http://127.0.0.1:4177";
const API_ORIGIN = window.location.protocol === "file:" ? DEFAULT_API_ORIGIN : window.location.origin;
const WS_ORIGIN = API_ORIGIN.replace(/^http/, "ws");
const FRAME_INTERVAL_MS = 1000;
const FRAME_WIDTH = 512;

if (window.location.protocol === "file:") {
  window.location.replace(`${API_ORIGIN}/index.html`);
}

let liveSocket = null;
let connectionPromise = null;
let generation = 0;
let processing = false;
let micPending = false;
let cameraPending = false;
let resetting = false;
const playbackSources = new Set();
let audioContext = null;
let inputProcessor = null;
let inputSource = null;
let audioStream = null;
let cameraStream = null;
let frameTimer = null;
let isRecording = false;
let nextPlaybackTime = 0;
let sessionId = null;
let state = null;
let writing = false;
const seenNotes = new Set();

const routeLabels = {
  emergency_escalation: ["Escalate to human", "danger"],
  policy_review: ["Policy review", "warning"],
  needs_docs: ["Needs docs", "warning"],
  special_investigation: ["SIU review", "info"],
  ready_for_adjuster: ["Ready for adjuster", "success"],
};

const blockerQuestions = {
  policyholder_name: "Name?",
  policy_number: "Policy number?",
  contact_method: "Best contact?",
  date_of_loss: "When did it happen?",
  loss_location: "Where?",
  loss_description: "What happened?",
};

const teamLabels = {
  lookup_policy: "Policy desk",
  sync_claim_packet: "Claim writer",
  pin_evidence_photo: "Evidence",
  draw_incident_sketch: "Sketch artist",
};

const emptyState = {
  route: "needs_docs",
  progress: 0,
  fields: {},
  transcript: [],
  events: [],
  tool_activity: [],
  missing_blockers: [],
  documents: [],
  evidence_photos: [],
  camera_notes: [],
  sketch: null,
  policy: null,
  handoff: {},
  packet_markdown: "# Adjuster handoff\n\nNo packet yet.",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function now() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function isFilled(field) {
  if (!field || field.status === "missing") return false;
  return !/^(missing:|not captured|not specified|unknown|none)/i.test(String(field.value || "").trim());
}

function shortBlocker(blocker) {
  if (blockerQuestions[blocker]) return blockerQuestions[blocker];
  let text = String(blocker).replace(/\s*\([^)]*\)/g, "").trim();
  if (text.length > 42) text = `${text.slice(0, 40).trim()}...`;
  return text.endsWith("?") ? text : `${text}?`;
}

function setStatus(text, tone = "") {
  callStatus.textContent = text;
  callStatus.className = `pill ${tone}`.trim();
}

function setWriting(next) {
  writing = next;
  penEl.hidden = !next;
}

function setState(nextState) {
  const previous = state || emptyState;
  state = {
    ...emptyState,
    ...nextState,
    tool_activity: nextState.tool_activity ?? previous.tool_activity,
  };
  render();
}

function render() {
  renderTranscript();
  renderNotes();
  renderPinboard();
  renderNeeded();
  renderTeam();
  renderStamp();
  document.querySelector("#downloadPacket").href = sessionId ? `${API_ORIGIN}/api/sessions/${sessionId}/packet` : "#";
  packetMarkdownEl.textContent = state.packet_markdown || emptyState.packet_markdown;
}

function renderTranscript() {
  transcriptEl.innerHTML = (state.transcript || [])
    .map((turn) => {
      const cls = turn.speaker === "Agent" ? "agent" : turn.speaker === "System" ? "system" : "claimant";
      const who = turn.speaker === "Agent" ? "AI" : turn.speaker === "System" ? "!" : "You";
      return `<article class="turn ${cls} ${turn.streaming ? "streaming" : ""}"><span class="who">${who}</span><p>${escapeHtml(turn.text)}</p></article>`;
    })
    .join("");
  transcriptEl.scrollTop = transcriptEl.scrollHeight;
}

function buildNotes() {
  const f = state.fields || {};
  const notes = [];
  const name = isFilled(f.claimant) ? f.claimant.value : "";
  const policy = isFilled(f.policy) ? f.policy.value : "";
  if (name || policy) {
    notes.push({ key: `title:${name}|${policy}`, cls: "title", text: [name, policy].filter(Boolean).join("  ·  ") });
  }
  const record = state.policy;
  if (record) {
    if (record.found) {
      const active = record.status === "active";
      const extras = (record.coverages || []).slice(0, 1).join("");
      notes.push({
        key: `policy:${record.policy_number}:${record.status}`,
        cls: active ? "check" : "flag urgent",
        text: active
          ? `${record.policy_line}, active. ${extras}`
          : `${record.policy_line}, ${record.status}. Human review before anything else.`,
      });
    } else {
      notes.push({ key: `policy:notfound:${record.policy_number}`, cls: "flag urgent", text: `Policy ${record.policy_number || ""} not found, confirm the number.` });
    }
  }
  const when = isFilled(f.date) ? f.date.value : "";
  const where = isFilled(f.location) ? f.location.value : "";
  if (when || where) {
    notes.push({ key: `whenwhere:${when}|${where}`, cls: "", text: [where, when].filter(Boolean).join(", ") });
  }
  if (isFilled(f.description)) {
    notes.push({ key: `desc:${f.description.value}`, cls: "", text: f.description.value });
  }
  if (isFilled(f.injuries)) {
    const urgent = f.injuries.status === "urgent";
    notes.push({ key: `inj:${f.injuries.value}`, cls: urgent ? "flag urgent" : "", text: urgent ? `Injury: ${f.injuries.value}` : f.injuries.value });
  }
  if (isFilled(f.contact)) {
    notes.push({ key: `contact:${f.contact.value}`, cls: "aside", text: `Reach at ${f.contact.value}` });
  }
  if (isFilled(f.photos)) {
    notes.push({ key: `ev:${f.photos.value}`, cls: "aside", text: `Has: ${f.photos.value}` });
  }
  if (isFilled(f.police)) {
    notes.push({ key: `rep:${f.police.value}`, cls: "aside", text: `Report: ${f.police.value}` });
  }
  if (claimantHasSpoken()) {
    const seenQuestions = new Set();
    for (const blocker of state.missing_blockers || []) {
      const question = shortBlocker(blocker);
      const dedupe = question.toLowerCase().replace(/[^a-z]/g, "");
      if (seenQuestions.has(dedupe) || seenQuestions.size >= 3) continue;
      seenQuestions.add(dedupe);
      notes.push({ key: `blank:${blocker}`, cls: "blank", text: question, blank: true });
    }
  }
  if (!notes.length) {
    notes.push({ key: "empty", cls: "aside", text: "Waiting for the claimant. Tap Talk, show the camera, or type below." });
  }
  return notes;
}

function claimantHasSpoken() {
  return (state.transcript || []).some((turn) => turn.speaker === "Claimant" && String(turn.text || "").trim());
}

function renderNotes() {
  const notes = buildNotes();
  notesEl.innerHTML = notes
    .map((note) => {
      const fresh = !seenNotes.has(note.key);
      seenNotes.add(note.key);
      return `<div class="note ${note.cls} ${fresh ? "ink-in" : ""}">${escapeHtml(note.text)}${note.blank ? '<span class="blank-line"></span>' : ""}</div>`;
    })
    .join("");
}

function renderPinboard() {
  const photos = state.evidence_photos || [];
  const sketch = state.sketch;
  const cards = photos.map(
    (photo, index) => `
      <figure class="polaroid" style="--tilt: ${index % 2 ? 2 : -2.5}deg" data-key="${escapeHtml(photo.id)}">
        <img src="${photo.data_url}" alt="Camera frame pinned as evidence" />
        <figcaption>${escapeHtml(photo.caption)}</figcaption>
        <span class="tag ${photo.confirmed ? "" : "unconfirmed"}">${photo.claimant_description ? `Claimant says: ${escapeHtml(photo.claimant_description)} · ` : ""}${photo.confirmed ? "Supported by this image" : "Claim not confirmed by this image"}</span>
        <span class="tag">Seen on camera ${escapeHtml(photo.captured_at || "")} · ${escapeHtml(photo.evidence_type || "evidence")}</span>
      </figure>`
  );
  if (sketch) {
    cards.push(`
      <figure class="polaroid sketch" style="--tilt: 1.5deg" data-key="sketch-${sketch.version}">
        <img src="${sketch.data_url}" alt="Hand drawn sketch of the incident scene" />
        <figcaption>Does this look right?</figcaption>
        <span class="tag">Sketch ${sketch.version}, drawn from what you described</span>
      </figure>`);
  }
  const currentKeys = [...pinboardEl.querySelectorAll("[data-key]")].map((el) => el.dataset.key).join("|");
  const nextKeys = [...photos.map((p) => p.id), sketch ? `sketch-${sketch.version}` : ""].filter(Boolean).join("|");
  if (currentKeys !== nextKeys) pinboardEl.innerHTML = cards.join("");
}

function renderStamp() {
  const route = state.route;
  const [label, tone] = routeLabels[route] || [route, "warning"];
  stampEl.hidden = !claimantHasSpoken() || writing;
  stampEl.textContent = label;
  if (stampEl.dataset.route !== route) {
    stampEl.dataset.route = route;
    stampEl.className = `stamp ${tone}`;
    stampEl.style.animation = "none";
    void stampEl.offsetWidth;
    stampEl.style.animation = "";
  }
}

function renderNeeded() {
  const items = [];
  for (const blocker of state.missing_blockers || []) {
    items.push({ text: shortBlocker(blocker).replace(/\?$/, ""), cls: "blocker" });
  }
  for (const doc of state.documents || []) {
    items.push({ text: `${doc.item} — ${doc.status || "unknown"}`, cls: doc.already_provided ? "done" : "" });
  }
  neededListEl.innerHTML = items.length
    ? items.map((item) => `<li class="${item.cls}"><span class="tick-box"></span><span>${escapeHtml(item.text)}</span></li>`).join("")
    : `<li class="empty">Nothing yet. The list fills in as the claim team reads the call.</li>`;
  const progress = Number(state.progress || 0);
  readinessEl.textContent = `${progress}% collected`;
  readinessEl.className = `pill ${progress >= 80 ? "" : progress >= 40 ? "warning" : "neutral"}`;
}

function renderTeam() {
  const activity = [...(state.tool_activity || [])].slice(-6).reverse();
  teamFeedEl.innerHTML = activity.length
    ? activity
        .map((item) => {
          const phase = item.phase || "running";
          let headline = item.headline || "";
          if (item.name === "sync_claim_packet" && phase === "done" && item.result) {
            const facts = (item.result.open_items || []).length;
            const docs = (item.result.open_documents || []).length;
            headline = `${String(item.result.routing_decision || "").replaceAll("_", " ")}: ${facts} open fact${facts === 1 ? "" : "s"}${docs ? ", documents still needed" : ""}`;
          }
          const meta = phase === "running" ? "working" : item.scheduling === "INTERRUPT" ? "interrupted the agent" : item.duration_ms != null ? `${item.duration_ms} ms` : "";
          return `<li><span class="team-dot ${phase}"></span><span><span class="team-name">${escapeHtml(teamLabels[item.name] || item.name)}</span> · ${escapeHtml(headline)}</span><span class="team-meta ${item.scheduling === "INTERRUPT" ? "interrupt" : ""}">${escapeHtml(meta)}</span></li>`;
        })
        .join("")
    : `<li class="empty">Policy desk, claim writer, evidence, and sketch artist will show up here as the agent calls them.</li>`;
  setWriting(processing || (state.tool_activity || []).some((item) => item.phase === "running"));
}

function appendSystem(text) {
  setState({ ...state, transcript: [...(state.transcript || []), { id: crypto.randomUUID(), speaker: "System", text }] });
}

function mergeTranscript(authoritative, local) {
  const byId = new Map((authoritative || []).map(turn => [turn.id, turn]));
  for (const turn of local || []) {
    if (!byId.has(turn.id)) byId.set(turn.id, turn);
  }
  return [...byId.values()];
}

function applyServerState(nextState) {
  if (nextState.session_id !== sessionId) return;
  setState({
    ...nextState,
    transcript: mergeTranscript(nextState.transcript, state?.transcript),
    tool_activity: mergeToolActivity(nextState.tool_activity, state?.tool_activity),
  });
}

function mergeToolActivity(authoritative, local) {
  const finished = new Set(["done", "error", "cancelled"]);
  const byId = new Map();
  for (const item of authoritative || []) byId.set(item.id, item);
  for (const item of local || []) {
    const current = byId.get(item.id);
    if (!current || (finished.has(item.phase) && !finished.has(current.phase))) byId.set(item.id, item);
  }
  return [...byId.values()];
}

function applyToolEvent(message) {
  const { type, ...entry } = message;
  const others = (state.tool_activity || []).filter((item) => item.id !== entry.id);
  setState({ ...state, tool_activity: [...others, entry] });
}

function upsertStreamingTurn(speaker, text, final = false, id = crypto.randomUUID()) {
  if (!String(text || "").trim()) return;
  const transcript = [...(state.transcript || [])];
  const index = transcript.findIndex(turn => turn.id === id);
  const turn = { id, speaker, text, streaming: !final };
  if (index >= 0) transcript[index] = turn;
  else transcript.push(turn);
  setState({ ...state, transcript });
}

async function api(path, options = {}) {
  const response = await fetch(`${API_ORIGIN}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `Request failed with status ${response.status}`);
  return payload;
}

function stopPlayback() {
  window.claimAvatar?.interrupt();
  for (const source of playbackSources) { try { source.stop(); } catch (_) {} }
  playbackSources.clear();
  nextPlaybackTime = audioContext?.currentTime || 0;
}

function clearBusy() {
  processing = false;
  state.tool_activity = (state.tool_activity || []).map(item => item.phase === "running" ? { ...item, phase: "cancelled", headline: "Connection ended" } : item);
  render();
}

function disconnectLive() {
  generation += 1;
  const socket = liveSocket;
  liveSocket = null;
  connectionPromise = null;
  stopLiveVoice(false);
  stopCamera();
  stopPlayback();
  window.claimAvatar?.reset();
  if (socket) socket.close();
  if (state) clearBusy();
}

async function createSession(resume = false) {
  if (resetting) return;
  resetting = true;
  newIntakeButton.disabled = true;
  const previous = sessionId || sessionStorage.getItem("intakeSession");
  disconnectLive();
  const epoch = generation;
  seenNotes.clear();
  setStatus("Connecting", "neutral");
  sessionId = null;
  setState(emptyState);
  pageDate.textContent = `Claim intake notes · ${new Date().toLocaleDateString([], { month: "short", day: "numeric" })}`;
  try {
    let payload;
    if (resume && previous) {
      try { payload = await api(`/api/sessions/${previous}`); } catch (_) { sessionStorage.removeItem("intakeSession"); }
    } else if (previous) {
      await api(`/api/sessions/${previous}`, { method: "DELETE" }).catch(() => {});
    }
    payload = payload || await api("/api/sessions", { method: "POST" });
    if (epoch !== generation) return;
    sessionId = payload.session_id;
    sessionStorage.setItem("intakeSession", sessionId);
    setState(payload.state);
    const health = await api("/api/health");
    window.claimAvatar?.configure(health.avatar);
    modelLabel.textContent = `${health.live_model} · sketches by ${health.sketch_model}`;
    setStatus(payload.has_api_key ? "Ready" : "API key required", payload.has_api_key ? "" : "danger");
    textInput.focus();
  } catch (error) {
    setStatus("Backend unavailable", "danger");
    appendSystem(error.message);
  } finally {
    resetting = false;
    newIntakeButton.disabled = false;
  }
}

function connectLive() {
  if (connectionPromise) return connectionPromise;
  if (!sessionId || resetting) return Promise.reject(new Error("Wait for the intake to be ready."));
  const epoch = generation;
  const avatarMode = window.claimAvatar?.supported === false ? "&avatar=off" : "";
  window.claimAvatar?.connecting();
  const socket = new WebSocket(`${WS_ORIGIN}/ws/live?session_id=${encodeURIComponent(sessionId)}${avatarMode}`);
  liveSocket = socket;
  connectionPromise = new Promise((resolve, reject) => {
    let ready = false;
    const timeout = setTimeout(() => { reject(new Error("Live connection timed out.")); socket.close(); }, 20000);
    const current = () => epoch === generation && liveSocket === socket;
    socket.onmessage = (event) => {
      if (!current()) return;
      const message = JSON.parse(event.data);
      if (message.session_id !== sessionId) return;
      if (message.type === "ready") {
        ready = true;
        clearTimeout(timeout);
        setStatus("Live", "");
        resolve();
      } else if (message.type === "session") {
        window.claimAvatar?.configure(message.avatar);
        modelLabel.textContent = `${message.model} · sketches by ${message.sketch_model}`;
      } else if (message.type === "processing") {
        processing = message.active;
        render();
      } else if (message.type === "transcript") {
        upsertStreamingTurn(message.speaker, message.text, message.final, message.id);
      } else if (message.type === "tool") {
        applyToolEvent(message);
      } else if (message.type === "audio") {
        playPcm24(message.data);
      } else if (message.type === "avatar_video") {
        window.claimAvatar?.append(message.data);
      } else if (message.type === "turn_complete") {
        window.claimAvatar?.finishTurn();
      } else if (message.type === "state") {
        applyServerState(message.state);
      } else if (message.type === "interrupted") {
        stopPlayback();
      } else if (message.type === "error") {
        processing = false;
        appendSystem(message.message);
        if (!ready) { reject(new Error(message.message)); socket.close(); }
      }
    };
    socket.onerror = () => { clearTimeout(timeout); reject(new Error("Live connection failed.")); socket.close(); };
    socket.onclose = () => {
      clearTimeout(timeout);
      if (!ready) reject(new Error("Live connection ended before it was ready."));
      if (!current()) return;
      liveSocket = null;
      connectionPromise = null;
      stopLiveVoice(false);
      stopCamera();
      stopPlayback();
      window.claimAvatar?.reset();
      clearBusy();
      setStatus("Disconnected — reconnect to continue", "warning");
    };
  });
  return connectionPromise;
}

async function unlockAudio() {
  if (window.AudioContext) {
    audioContext = audioContext || new AudioContext();
    await audioContext.resume();
  }
}

async function sendClaimantTurn(text) {
  const epoch = generation;
  try {
    stopPlayback();
    await unlockAudio();
    await connectLive();
    if (epoch !== generation) return;
    const id = crypto.randomUUID();
    liveSocket.send(JSON.stringify({ type: "text", text, id }));
    upsertStreamingTurn("Claimant", text, true, id);
    processing = true;
    render();
  } catch (error) {
    if (epoch !== generation) return;
    textInput.value = text;
    appendSystem(`${error.message} Your message is back in the input; send it again to retry.`);
  }
}

async function startLiveVoice() {
  if (micPending || isRecording) return;
  const epoch = generation;
  if (!navigator.mediaDevices?.getUserMedia || !window.AudioContext) {
    appendSystem("This browser cannot capture microphone audio. Type instead.");
    return;
  }
  try {
    micPending = true;
    await unlockAudio();
    await connectLive();
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    });
    if (epoch !== generation || !liveSocket || liveSocket.readyState !== WebSocket.OPEN) { stream.getTracks().forEach(track => track.stop()); return; }
    audioStream = stream;
    audioContext = audioContext || new AudioContext();
    await audioContext.resume();
    inputSource = audioContext.createMediaStreamSource(audioStream);
    inputProcessor = audioContext.createScriptProcessor(4096, 1, 1);
    inputProcessor.onaudioprocess = (event) => {
      event.outputBuffer.getChannelData(0).fill(0);
      if (!liveSocket || liveSocket.readyState !== WebSocket.OPEN) return;
      const pcm16 = resampleToPcm16(event.inputBuffer.getChannelData(0), audioContext.sampleRate, 16000);
      liveSocket.send(JSON.stringify({ type: "audio", data: arrayBufferToBase64(pcm16.buffer) }));
    };
    inputSource.connect(inputProcessor);
    inputProcessor.connect(audioContext.destination);
    isRecording = true;
    micButton.classList.add("active");
    micButton.querySelector(".round-label").textContent = "Listening";
    setStatus("Live, listening", "");
  } catch (error) {
    const denied = error.name === "NotAllowedError" || /denied|permission/i.test(error.message);
    appendSystem(denied ? "Microphone access was denied. Allow it for this site or type instead." : `Voice failed: ${error.message}`);
    stopLiveVoice(false);
  } finally { micPending = false; }
}

function stopLiveVoice(closeSocket = true) {
  isRecording = false;
  micButton.classList.remove("active");
  micButton.querySelector(".round-label").textContent = "Talk";
  inputProcessor?.disconnect();
  inputSource?.disconnect();
  audioStream?.getTracks().forEach((track) => track.stop());
  inputProcessor = null;
  inputSource = null;
  audioStream = null;
  if (closeSocket) {
    disconnectLive();
    setStatus("Call ended — intake saved for reconnect", "neutral");
  }
}

async function startCamera() {
  if (cameraPending || cameraStream) return;
  const epoch = generation;
  if (!navigator.mediaDevices?.getUserMedia) {
    appendSystem("This browser cannot access a camera.");
    return;
  }
  try {
    cameraPending = true;
    await unlockAudio();
    await connectLive();
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "environment" } });
    if (epoch !== generation || !liveSocket || liveSocket.readyState !== WebSocket.OPEN) { stream.getTracks().forEach(track => track.stop()); return; }
    cameraStream = stream;
    stream.getVideoTracks().forEach(track => track.addEventListener("ended", stopCamera, { once: true }));
    liveSocket.send(JSON.stringify({ type: "camera_state", enabled: true }));
    cameraPreview.srcObject = cameraStream;
    cameraStage.hidden = false;
    cameraButton.classList.add("active");
    cameraButton.querySelector(".round-label").textContent = "Stop camera";
    frameTimer = window.setInterval(sendFrame, FRAME_INTERVAL_MS);
    if (!isRecording) setStatus("Camera on, agent can see", "");
  } catch (error) {
    const denied = error.name === "NotAllowedError" || /denied|permission/i.test(error.message);
    appendSystem(denied ? "Camera access was denied. Allow it for this site to show the damage." : `Camera failed: ${error.message}`);
    stopCamera();
  } finally { cameraPending = false; }
}

function stopCamera() {
  const wasOn = Boolean(cameraStream);
  if (frameTimer) window.clearInterval(frameTimer);
  frameTimer = null;
  cameraStream?.getTracks().forEach((track) => track.stop());
  cameraStream = null;
  cameraPreview.srcObject = null;
  cameraStage.hidden = true;
  cameraButton.classList.remove("active");
  cameraButton.querySelector(".round-label").textContent = "Show camera";
  if (wasOn && liveSocket?.readyState === WebSocket.OPEN) {
    liveSocket.send(JSON.stringify({ type: "camera_state", enabled: false }));
    if (!isRecording) setStatus("Camera off, describing the scene", "");
  }
}

function sendFrame() {
  if (!cameraStream || !liveSocket || liveSocket.readyState !== WebSocket.OPEN) return;
  if (!cameraPreview.videoWidth) return;
  const scale = FRAME_WIDTH / cameraPreview.videoWidth;
  frameCanvas.width = FRAME_WIDTH;
  frameCanvas.height = Math.round(cameraPreview.videoHeight * scale);
  const ctx = frameCanvas.getContext("2d");
  ctx.drawImage(cameraPreview, 0, 0, frameCanvas.width, frameCanvas.height);
  const dataUrl = frameCanvas.toDataURL("image/jpeg", 0.6);
  liveSocket.send(JSON.stringify({ type: "video", data: dataUrl.split(",")[1] }));
}

function resampleToPcm16(input, inputRate, outputRate) {
  const ratio = inputRate / outputRate;
  const outputLength = Math.floor(input.length / ratio);
  const pcm = new Int16Array(outputLength);
  for (let i = 0; i < outputLength; i += 1) {
    const index = i * ratio;
    const before = Math.floor(index);
    const after = Math.min(before + 1, input.length - 1);
    const weight = index - before;
    const sample = Math.max(-1, Math.min(1, input[before] * (1 - weight) + input[after] * weight));
    pcm[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
  }
  return pcm;
}

function arrayBufferToBase64(buffer) {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.byteLength; i += 1) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

function playPcm24(base64) {
  audioContext = audioContext || new AudioContext();
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  const pcm = new Int16Array(bytes.buffer);
  const audioBuffer = audioContext.createBuffer(1, pcm.length, 24000);
  const channel = audioBuffer.getChannelData(0);
  for (let i = 0; i < pcm.length; i += 1) channel[i] = pcm[i] / 32768;
  const source = audioContext.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(audioContext.destination);
  const startAt = Math.max(audioContext.currentTime, nextPlaybackTime);
  playbackSources.add(source);
  source.onended = () => playbackSources.delete(source);
  source.start(startAt);
  nextPlaybackTime = startAt + audioBuffer.duration;
}

micButton.addEventListener("click", () => (isRecording ? stopLiveVoice() : startLiveVoice()));
cameraButton.addEventListener("click", () => (cameraStream ? stopCamera() : startCamera()));
newIntakeButton.addEventListener("click", () => createSession(false));
window.addEventListener("pagehide", disconnectLive);
textForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = textInput.value.trim();
  if (!value) return;
  textInput.value = "";
  sendClaimantTurn(value);
});
document.querySelector("#openPacket").addEventListener("click", () => packetDialog.showModal());
document.querySelector("#closePacket").addEventListener("click", () => packetDialog.close());
if (window.claimAvatar) {
  window.claimAvatar.onFallback = () => {
    disconnectLive();
    setStatus("Voice mode — tap Talk to reconnect", "neutral");
  };
}

createSession(true);
