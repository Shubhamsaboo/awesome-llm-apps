import { logo as icon } from "./logo.js";
export function createUI(actions) {
  const host = document.createElement("div");
  host.id = "ripple-native";
  host.dataset.build = "review-continuity-4";
  host.style.cssText =
    "position:fixed;inset:0;z-index:2147483000;pointer-events:none;";
  const root = host.attachShadow({ mode: "open" });
  root.innerHTML = `<style>
  :host{font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#233c3e;--accent:#176c62;--muted:#5d6e70;--line:#e3e9e7;--red:#a84336;--green:#176c62;color-scheme:light}*{box-sizing:border-box}button,textarea{font:inherit}button{cursor:pointer;color:inherit}button:disabled{cursor:default;opacity:.5}button:focus-visible,summary:focus-visible{outline:3px solid #21887b;outline-offset:3px}button:active:not(:disabled){transform:translateY(1px)}[hidden]{display:none!important}p{margin:0}small{font-size:12px;color:var(--muted)}svg{display:block;flex-shrink:0}
  #dock{position:fixed;right:24px;bottom:24px;display:flex;align-items:center;max-width:calc(100vw - 32px);padding:5px;background:#fff;border:1px solid var(--line);border-radius:17px;box-shadow:0 4px 18px #163f4014;pointer-events:auto}#chip{display:flex;align-items:center;gap:10px;border:0;background:none;min-height:42px;padding:3px 12px 3px 3px;border-radius:12px;text-align:left;min-width:0}#chip:hover{background:#f1f7f5}#chip>svg{width:32px;height:32px}#label{font-size:13px;font-weight:550;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}#count{font-size:12px;font-weight:700;min-width:23px;height:23px;padding:2px 6px;border-radius:7px;background:#fff0d9;color:#815716;font-variant-numeric:tabular-nums}#settings{width:36px;height:36px;border:0;border-left:1px solid var(--line);border-radius:0 9px 9px 0;background:none;color:var(--muted);display:grid;place-items:center}#settings:hover{background:#f1f7f5}#chip[data-state="error"]{color:var(--red)}#chip[data-state="busy"] #status-dot{background:#c18726}#status-dot{width:6px;height:6px;border-radius:50%;background:var(--accent);flex-shrink:0}#chip[data-state="paused"] #status-dot{background:#8a9898}
  #menu,#card{position:fixed;width:392px;max-width:calc(100vw - 32px);max-height:calc(100dvh - 32px);overflow:auto;background:#fff;border:1px solid var(--line);border-radius:18px;box-shadow:0 12px 40px #143b4024,0 2px 8px #143b400c;pointer-events:auto}#menu{right:24px;bottom:88px;padding:24px}h2{font-size:19px;letter-spacing:-.5px;line-height:1.3;margin:0;font-weight:650}.brand{display:flex;align-items:center;gap:9px;font-size:13px;font-weight:650;letter-spacing:-.2px}.brand svg{width:25px;height:25px}.menu-brand{margin-bottom:20px}.brand-note{margin-left:auto;font-size:11px;font-weight:500;color:var(--muted)}#detail{color:var(--muted);margin:12px 0 18px;text-wrap:pretty}#privacy{display:block;border-top:1px solid var(--line);padding-top:14px;font-size:12px;line-height:1.6}.journey{display:flex;align-items:center;gap:6px;color:var(--accent);font-size:11px;font-weight:600;margin:16px 0 20px}.journey span{padding:6px 8px;background:#edf6f2;border-radius:6px}.journey i{color:#728788;font-style:normal}
  .primary{background:var(--accent);color:#fff;border:1px solid transparent;border-radius:10px;min-height:42px;padding:9px 16px;font-weight:600}.primary:hover{background:#10594f}.text{border:0;background:none;min-height:40px;padding:8px 10px;border-radius:9px;color:var(--muted);font-size:13px}.text:hover{background:#f0f5f3;color:#233c3e}.actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:18px}.card-head{display:flex;align-items:center;padding:16px 18px;border-bottom:1px solid var(--line);gap:10px}#counter{margin-left:auto;font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}.close{border:0;background:none;border-radius:8px;width:30px;height:30px;display:grid;place-items:center;color:var(--muted)}.close:hover{background:#edf4f1}.card-body{padding:20px}.eyebrow{display:flex;align-items:center;gap:6px;font-size:11px;font-weight:650;letter-spacing:.03em;margin-bottom:8px}.symbol{font-size:15px;line-height:12px;font-weight:500}.comparison{margin-top:18px;position:relative}.original{padding:13px 15px;background:#fff5f1;border:1px solid #f4dfd5;border-radius:10px 10px 0 0;color:var(--red)}.target{font-size:14px;color:#703f37;max-height:130px;overflow:auto;overflow-wrap:anywhere;line-height:1.65}.draft{padding:13px 15px;background:#edf7f2;border:1px solid #cbe4d8;border-top:0;border-radius:0 0 10px 10px}.draft .eyebrow{color:#176c62;justify-content:space-between}.draft label{display:flex;align-items:center;gap:6px}.edit-hint{font-size:11px;color:#517567;font-weight:400;letter-spacing:0}textarea{display:block;width:100%;min-height:78px;max-height:210px;resize:vertical;border:1px solid transparent;border-radius:5px;background:transparent;padding:2px 0;color:#214e43;line-height:1.65;outline-offset:4px}textarea:hover{border-color:#b7d7c8}textarea:focus{outline:2px solid #21887b;background:#fff;padding:6px}#suggestion-status{display:block;font-size:12px;line-height:1.6;margin-top:12px;color:var(--muted)}#suggestion-status[data-error="true"]{color:var(--red)}#skeleton{height:75px;display:flex;flex-direction:column;gap:9px;padding:8px 0}#skeleton span{height:8px;border-radius:4px;background:#cfe5db;width:94%}#skeleton span:nth-child(2){width:79%}#skeleton span:nth-child(3){width:45%}#source{margin-top:16px;border-top:1px solid var(--line);padding-top:12px}summary{font-size:12px;color:var(--muted);cursor:pointer;min-height:28px;padding:4px 0}.quotes{padding:8px 0 0 13px;font-size:12px;overflow-wrap:anywhere;max-height:170px;overflow:auto;border-left:2px solid #d7e6df;margin-top:8px}.quotes p{margin:5px 0 10px}.quotes small{font-size:10px;font-weight:650}.before{color:#9b574c;text-decoration:line-through;text-decoration-color:#d89a8b}#after{color:#176c62}.card-footer{display:flex;gap:8px;align-items:center;border-top:1px solid var(--line);padding:14px 18px;background:#fbfcfb}.card-footer .primary{flex:1}#next{width:38px;min-width:38px;display:grid;place-items:center;border:1px solid var(--line);padding:0}.review-note{font-size:11px;color:#667878;margin-top:12px}
  .under{position:fixed;background:#d28b4c;height:2px;pointer-events:none;border-radius:2px}.under.active{background:#176c62;height:3px}.mark{position:fixed;width:28px;height:28px;padding:0;background:#fff5e8;border:1px solid #dfb27f;border-radius:9px;pointer-events:auto;color:#805117;display:grid;place-items:center;font-size:12px;font-weight:650;font-variant-numeric:tabular-nums;box-shadow:0 1px 3px #5036120f}.mark:hover,.mark[aria-pressed="true"]{background:#176c62;color:#fff;border-color:#176c62}.mark:focus-visible{outline:3px solid #21887b;outline-offset:3px}#live{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}@media(max-width:600px){#dock{right:16px;bottom:16px}#menu{right:16px;bottom:82px}#label{max-width:190px}.card-body{padding:16px}.card-footer{padding:12px}.edit-hint{display:none}}@media(prefers-reduced-motion:no-preference){button{transition:background .15s ease,color .15s ease,transform .15s ease}#card:not([hidden]),#menu:not([hidden]){animation:arrive .16s ease-out}#skeleton{animation:breathe 1.4s ease-in-out infinite}#chip[data-state="busy"] #status-dot{animation:breathe 1.4s ease-in-out infinite}@keyframes arrive{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}@keyframes breathe{50%{opacity:.45}}}
  .remove-target{text-decoration:line-through;text-decoration-color:#c17d6e}.remove-note{display:block;color:#854a3f;font-weight:550;padding:5px 0}
  </style>
  <div id="marks"></div>
  <div id="dock"><button id="chip" aria-label="Ripple status and results" aria-expanded="false">${icon}<span id="status-dot" aria-hidden="true"></span><span id="label">Enable Ripple</span><span id="count" hidden aria-hidden="true"></span></button><button id="settings" aria-label="Ripple settings" aria-expanded="false" aria-controls="menu"><svg viewBox="0 0 20 20" width="18" height="18" fill="none" aria-hidden="true"><path d="M4 5h12M4 10h12M4 15h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M7 3v4M13 8v4M8 13v4" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg></button></div>
  <section id="menu" hidden aria-label="Ripple settings"><div class="brand menu-brand">${icon}ripple<span class="brand-note">In this Google Doc</span></div><h2>One edit. Everything connected.</h2><p id="detail">Change a fact. Ripple finds related sentences and suggests how to update them.</p><div class="journey" aria-label="Edit, spot related text, review"><span>01 Edit</span><i aria-hidden="true">→</i><span>02 Spot</span><i aria-hidden="true">→</i><span>03 Review</span></div><small id="privacy">Jev checks document text. Gemini drafts corrections using flagged passages and nearby context. Both API keys stay on this computer.</small><div class="actions"><button class="primary" id="toggle">Enable for this Doc</button><button class="text" id="menu-pause" hidden>Pause</button><button class="text" id="restore" hidden>Restore kept</button></div></section>
  <section id="card" hidden role="dialog" aria-modal="false" aria-labelledby="question"><header class="card-head"><div class="brand">${icon}ripple</div><span id="counter"></span><button class="close" aria-label="Close prompt" id="close"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="m4 4 8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5"/></svg></button></header><div class="card-body"><h2 id="question">Keep this in sync</h2><div class="comparison"><div class="original"><div class="eyebrow"><span class="symbol" aria-hidden="true">−</span> Current wording</div><p class="target" id="target"></p></div><div class="draft"><div class="eyebrow"><label for="replacement"><span class="symbol" aria-hidden="true">+</span> <span id="suggestion-heading">Suggested wording</span></label><span class="edit-hint" id="edit-hint">Click to edit</span></div><div id="skeleton" aria-hidden="true"><span></span><span></span><span></span></div><textarea id="replacement" spellcheck="true" aria-describedby="suggestion-status" hidden></textarea><small id="no-replacement" hidden>More information is needed to write a correction.</small></div></div><small id="suggestion-status" role="status">Drafting a correction…</small><button class="text" id="retry-suggestion" hidden>Retry suggestion</button><button class="text" id="copy" hidden>Copy suggestion</button><details id="source"><summary>Why this sentence?</summary><div class="quotes"><small>You changed</small><p class="before" id="before"></p><small>To</small><p id="after"></p></div></details><p class="review-note">Only applied when you choose.</p></div><footer class="card-footer"><button class="primary" id="apply" disabled>Apply change</button><button class="text" id="keep">Keep original</button><button class="text" id="next" aria-label="Next suggestion" title="Next suggestion"><svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M4 10h12m-5-5 5 5-5 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></button></footer></section><div id="live" role="status" aria-live="polite"></div>`;
  document.documentElement.append(host);
  const get = (id) => root.getElementById(id),
    chip = get("chip"),
    menu = get("menu"),
    card = get("card");
  const drafts = new Map();
  let applying = false;
  let enabled = false,
    error = "",
    rows = [],
    active = null,
    rectangles = new Map();
  const close = () => {
    card.hidden = true;
    active = null;
    chip.setAttribute("aria-expanded", "false");
    refreshMarks();
  };
  const settings = get("settings");
  function toggleMenu(force) {
    close();
    menu.hidden = force === undefined ? !menu.hidden : !force;
    settings.setAttribute("aria-expanded", String(!menu.hidden));
    chip.setAttribute("aria-expanded", String(!menu.hidden));
  }
  settings.onclick = () => toggleMenu();
  get("source").ontoggle = () => {
    if (active) position(rectangles.get(active.key)?.[0]);
  };
  get("close").onclick = () => {
    close();
    chip.focus();
  };
  chip.onclick = () => {
    if (rows.length && !error && menu.hidden) {
      show(rows[0]);
      return;
    }
    toggleMenu();
  };
  chip.oncontextmenu = (e) => {
    e.preventDefault();
    toggleMenu();
  };
  chip.onkeydown = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      toggleMenu(true);
      get("toggle").focus();
    }
  };
  get("toggle").onclick = () => {
    menu.hidden = true;
    settings.setAttribute("aria-expanded", "false");
    chip.setAttribute("aria-expanded", "false");
    if (error && enabled) actions.retry();
    else actions.toggle(!enabled);
  };
  get("menu-pause").onclick = () => {
    menu.hidden = true;
    settings.setAttribute("aria-expanded", "false");
    chip.setAttribute("aria-expanded", "false");
    actions.toggle(false);
  };
  get("restore").onclick = () => {
    actions.restore();
    menu.hidden = true;
    settings.setAttribute("aria-expanded", "false");
    chip.setAttribute("aria-expanded", "false");
  };
  get("replacement").oninput = () => {
    if (active) {
      drafts.set(active.key, get("replacement").value);
      get("apply").disabled = applying || !get("replacement").value.trim();
    }
  };
  get("retry-suggestion").onclick = () => {
    if (active) actions.retrySuggestion(active);
  };
  get("copy").onclick = async () => {
    try {
      await navigator.clipboard.writeText(get("replacement").value);
      get("suggestion-status").textContent =
        "Copied. Replace the sentence directly in your Doc.";
    } catch {
      get("replacement").focus();
      get("replacement").select();
      get("suggestion-status").textContent =
        "Select and copy the wording, then paste it into your Doc.";
    }
  };
  // Preserve Docs focus on mouse clicks; the bridge also restores its editing target.
  get("apply").onmousedown = (e) => {
    if (e.button === 0) e.preventDefault();
  };
  get("apply").onclick = async () => {
    if (!active || applying) return;
    const row = active,
      index = rows.findIndex((r) => r.key === row.key),
      deleting = row.suggestion?.action === "delete";
    applying = true;
    get("apply").disabled = true;
    get("apply").textContent = deleting ? "Removing…" : "Applying…";
    let result;
    try {
      result = await actions.apply(
        row,
        deleting ? "" : get("replacement").value.trim(),
        deleting ? "delete" : "replace",
      );
    } catch {
      result = {
        ok: false,
        error:
          "Could not confirm the change. Check the Doc before trying again.",
      };
    }
    applying = false;
    get("apply").textContent = deleting ? "Remove sentence" : "Apply change";
    if (result.ok) {
      drafts.delete(row.key);
      if (active?.key === row.key && !card.hidden) {
        const next = rows[Math.min(index, rows.length - 1)];
        if (next) show(next, true);
        else close();
      }
    } else if (active?.key === row.key) {
      get("suggestion-status").dataset.error = "true";
      get("suggestion-status").textContent = result.error;
      get("copy").hidden = deleting;
      get("apply").disabled = !deleting && !get("replacement").value.trim();
    }
  };
  get("keep").onclick = () => {
    if (active) {
      actions.keep(active);
      close();
    }
  };
  get("next").onclick = () => {
    const i = rows.findIndex((f) => f.key === active?.key);
    const row = rows[(i + 1) % rows.length];
    if (row) show(row, true);
  };
  const outside = (e) => {
    if (!e.composedPath().includes(host)) {
      close();
      menu.hidden = true;
      settings.setAttribute("aria-expanded", "false");
      chip.setAttribute("aria-expanded", "false");
    }
  };
  document.addEventListener("pointerdown", outside, true);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const wasOpen = !card.hidden || !menu.hidden;
      close();
      menu.hidden = true;
      settings.setAttribute("aria-expanded", "false");
      if (wasOpen) chip.focus();
    }
  });
  function position(rect) {
    const w = Math.min(392, innerWidth - 32);
    let x = rect ? rect.right + 18 : innerWidth - w - 24;
    if (x + w > innerWidth - 16)
      x = Math.max(16, (rect?.left ?? innerWidth) - w - 18);
    let y = rect ? rect.top : innerHeight - card.offsetHeight - 80;
    y = Math.max(16, Math.min(y, innerHeight - card.offsetHeight - 16));
    card.style.left = x + "px";
    card.style.top = y + "px";
  }
  function show(row, navigate = false) {
    active = row;
    menu.hidden = true;
    settings.setAttribute("aria-expanded", "false");
    card.hidden = false;
    chip.setAttribute("aria-expanded", "true");
    get("source").open = false;
    get("target").textContent = row.text;
    get("before").textContent = row.source.before;
    get("after").textContent = row.source.after;
    get("counter").textContent =
      rows.findIndex((f) => f.key === row.key) + 1 + " / " + rows.length;
    renderSuggestion(row);
    const rect = rectangles.get(row.key)?.[0];
    position(rect);
    refreshMarks();
    if (navigate || !rect) actions.navigate(row.text);
  }
  function state(s) {
    enabled = s.enabled;
    error = s.error || "";
    get("label").textContent =
      rows.length && !error && /may need updating/.test(s.label)
        ? "Review changes"
        : s.label;
    chip.dataset.state = error
      ? "error"
      : !enabled
        ? "paused"
        : /…$/.test(s.label)
          ? "busy"
          : "ready";
    get("live").textContent = s.announce || "";
    get("detail").textContent =
      error ||
      s.detail ||
      "Edit normally. Ripple checks after you pause and marks sentences that may need updating.";
    get("privacy").hidden = enabled;
    get("toggle").textContent =
      error && enabled
        ? "Retry"
        : enabled
          ? "Pause for this Doc"
          : "Enable for this Doc";
    get("restore").hidden = !s.kept;
    get("menu-pause").hidden = !(enabled && error);
    get("toggle").disabled = !!s.disabled;
  }
  function renderSuggestion(row) {
    const ready = row.suggestionState === "ready",
      action = row.suggestion?.action || "replace",
      deleting = ready && action === "delete",
      canReplace = ready && action === "replace",
      value = drafts.get(row.key) ?? row.suggestion?.replacement ?? "";
    get("replacement").hidden =
      !canReplace || (!value.trim() && !drafts.has(row.key));
    if (get("replacement").value !== value) get("replacement").value = value;
    get("suggestion-status").textContent =
      row.suggestionState === "error"
        ? row.suggestionError
        : ready
          ? row.suggestion.reason
          : "Drafting a correction…";
    get("retry-suggestion").hidden = row.suggestionState !== "error";
    get("apply").disabled =
      applying || !(deleting || (canReplace && value.trim()));
    if (!applying)
      get("apply").textContent = deleting ? "Remove sentence" : "Apply change";
    get("suggestion-heading").textContent = deleting
      ? "Suggested removal"
      : ready && action === "keep"
        ? "Keep this sentence"
        : ready && action === "needs_info"
          ? "Needs your input"
          : "Suggested wording";
    get("target").classList.toggle("remove-target", deleting);
    get("no-replacement").classList.toggle("remove-note", deleting);
    get("copy").hidden = true;
    get("edit-hint").hidden = !canReplace || !value.trim();
    get("skeleton").hidden = row.suggestionState !== "loading";
    get("no-replacement").textContent =
      row.suggestionState === "error"
        ? "The correction is unavailable. Try again below."
        : deleting
          ? "Remove this sentence. No replacement is needed."
          : action === "keep"
            ? "This sentence still fits the updated document."
            : "More information is needed to write a correction.";
    get("no-replacement").hidden =
      row.suggestionState === "loading" || (canReplace && !!value.trim());
    get("suggestion-status").dataset.error = String(
      row.suggestionState === "error",
    );
    get("next").disabled = rows.length < 2;
    position(rectangles.get(row.key)?.[0]);
  }
  function results(findings) {
    rows = findings;
    get("count").textContent = String(rows.length);
    get("count").hidden = !rows.length;
    if (active) {
      const fresh = rows.find((r) => r.key === active.key);
      if (!fresh) {
        if (!applying) close();
      } else {
        active = fresh;
        get("counter").textContent =
          rows.findIndex((f) => f.key === fresh.key) + 1 + " / " + rows.length;
        renderSuggestion(fresh);
      }
    }
  }

  function draw(mapped) {
    rectangles = mapped;
    const layer = get("marks");
    layer.replaceChildren();
    for (const [index, row] of rows.entries()) {
      const rects = mapped.get(row.key) || [];
      for (const rect of rects) {
        const el = document.createElement("div");
        el.className = "under";
        el.dataset.key = row.key;
        el.style.cssText = `left:${rect.left}px;top:${rect.bottom + 1}px;width:${rect.width}px`;
        layer.append(el);
      }
      if (rects.length) {
        const rect = rects[0],
          button = document.createElement("button");
        button.className = "mark";
        button.setAttribute(
          "aria-label",
          "Review possible inconsistency: " + row.text,
        );
        button.title = "Review suggestion " + (index + 1);
        button.textContent = String(index + 1);
        button.dataset.key = row.key;
        button.setAttribute("aria-pressed", String(active?.key === row.key));
        button.style.cssText = `left:${Math.max(2, rect.left - 34)}px;top:${rect.top - 5}px`;
        button.onclick = () => show(row);
        layer.append(button);
      }
    }
    refreshMarks();
    if (active && !card.hidden) position(mapped.get(active.key)?.[0]);
  }
  function refreshMarks() {
    for (const mark of get("marks").querySelectorAll("[data-key]")) {
      const selected = mark.dataset.key === active?.key;
      mark.classList.toggle("active", selected);
      if (mark.tagName === "BUTTON")
        mark.setAttribute("aria-pressed", String(selected));
    }
  }
  return {
    state,
    results,
    draw,
    close,
    remove: () => {
      host.remove();
      document.removeEventListener("pointerdown", outside, true);
    },
    root,
  };
}
