(async () => {
  if (document.getElementById("ripple-native")) return;
  const { createUI } = await import(chrome.runtime.getURL("ui.js"));
  const { reconcile, uniqueSpan, sentences, fingerprint } = await import(
    chrome.runtime.getURL("core.js")
  );
  const channel = "ripple-docs-v1";
  let enabled = false,
    current = "",
    processed = "",
    sources = [],
    findings = [],
    visible = [],
    kept = new Set(),
    timer,
    revision = 0,
    running = false,
    tab = "",
    error = "",
    starting = false,
    paintedRevision = -1,
    composing = false,
    snapshotValid = false;
  const pendingApplies = new Map();
  let activeApply = null;
  let corrections = [];
  const docId = location.pathname.match(/\/document\/d\/([^/]+)/)?.[1];
  const storageKey = "enabled:" + docId;
  const send = (message) =>
    window.postMessage({ channel, ...message }, location.origin);
  const rpc = async (message) => {
    try {
      return await chrome.runtime.sendMessage(message);
    } catch {
      return {
        ok: false,
        error: "Ripple was updated. Reload this Google Doc to reconnect.",
      };
    }
  };
  const ui = createUI({
    toggle,
    apply: applySuggestion,
    retrySuggestion: (row) => generateSuggestions([row], revision, current),
    retry: async () => {
      const health = await rpc({ type: "health" });
      if (!health.ok || !health.ready) {
        error = health.error || "Add a TypeSafe API key to the local service.";
        state("Could not connect");
        return;
      }
      error = "";
      starting = !processed;
      send({ type: "enabled", enabled: true });
      schedule(0, true);
    },
    keep(row) {
      kept.add(row.key);
      publish();
    },
    restore() {
      kept.clear();
      publish();
    },
    navigate(quote) {
      send({ type: "navigate", quote });
    },
  });
  if (ui.root?.host)
    ui.root.host.dataset.controllerBuild = "review-continuity-4";
  function state(label, extra = {}) {
    ui.state({ enabled, error, kept: kept.size, label, ...extra });
  }
  function reset() {
    clearTimeout(timer);
    revision++;
    paintedRevision = -1;
    snapshotValid = false;
    current = "";
    processed = "";
    sources = [];
    corrections = [];
    findings = [];
    visible = [];
    kept.clear();
    error = "";
    ui.results([]);
    ui.draw(new Map());
    ui.close();
  }
  async function toggle(on) {
    enabled = on;
    reset();
    chrome.storage.local.set({ [storageKey]: on });
    send({ type: "enabled", enabled: false });
    if (!on) {
      state("Ripple paused", {
        detail:
          "Resume to capture a fresh baseline. Edits while paused are not tracked.",
      });
      return;
    }
    starting = true;
    state("Connecting…", { disabled: true });
    const health = await rpc({ type: "health" });
    if (!enabled) return;
    if (!health.ok || !health.ready) {
      error =
        health.error || "Add a TypeSafe API key to the local Ripple service.";
      state("Could not connect");
      return;
    }
    state("Reading this Doc…");
    send({ type: "enabled", enabled: true });
  }
  function publish() {
    paintedRevision = revision;
    visible = findings.filter((f) => !kept.has(f.key));
    ui.results(visible);
    paint();
    if (error) {
      state("Could not check");
      return;
    }
    const n = visible.length;
    state(
      n
        ? `${n} ${n === 1 ? "place" : "places"} may need updating`
        : sources.length
          ? "No likely inconsistencies found"
          : "Ready for your next edit",
      {
        detail:
          "Checks cover the active document tab. Other tabs, images, drawings, footnotes, and comments are not checked.",
        announce: n ? `${n} places may need updating.` : "",
      },
    );
  }
  function schedule(delay = 1900, force = false) {
    clearTimeout(timer);
    if (enabled) timer = setTimeout(() => check(force), delay);
  }
  async function check(force = false) {
    if (!enabled || !snapshotValid || !current || starting || composing) return;
    if (running || activeApply) {
      schedule(600, force);
      return;
    }
    if (!force && current === processed) return;
    running = true;
    const rev = revision,
      snapshot = current;
    try {
      const undo = corrections.findLast(
        (c) => c.after === processed && c.before === snapshot,
      );
      const redo = corrections.findLast(
        (c) => c.before === processed && c.after === snapshot,
      );
      sources = undo
        ? [...undo.sourcesBefore]
        : redo
          ? [...redo.sourcesAfter]
          : reconcile(processed, snapshot, sources, findings);
      processed = snapshot;
      if (!sources.length) {
        findings = [];
        error = "";
        publish();
        return;
      }
      const all = sentences(snapshot);
      if (all.length > 120)
        throw new Error(
          "This prototype supports up to 120 sentences in the active tab. Nothing was sent.",
        );
      if (all.some((s) => s.text.length > 2500))
        throw new Error(
          "One paragraph is too long for this prototype. Split it into shorter sentences.",
        );
      paintedRevision = -1;
      ui.results([]);
      ui.draw(new Map());
      error = "";
      state("Checking your change…");
      const next = [];
      for (const source of sources) {
        const span = uniqueSpan(snapshot, source.after);
        if (!span)
          throw new Error(
            "The changed wording could not be located uniquely. Pause and resume Ripple to start with a fresh baseline.",
          );
        const candidates = all.filter(
          (s) => s.end <= span.start || s.start >= span.end,
        );
        if (!candidates.length) continue;
        if (ui.root?.host)
          ui.root.host.dataset.checkRequests = String(
            Number(ui.root.host.dataset.checkRequests || 0) + 1,
          );
        const answer = await rpc({
          type: "check",
          input: {
            source: { before: source.before, after: source.after },
            sentences: candidates.map(({ id, text, section }) => ({
              id,
              text,
              section,
            })),
          },
        });
        if (rev !== revision || !enabled || !snapshotValid) return;
        if (!answer.ok) {
          const failure = new Error(answer.error);
          failure.retryable = answer.retryable === true;
          throw failure;
        }
        for (const result of answer.results || []) {
          if (result.status !== "likely_conflict") continue;
          const s = candidates.find((s) => s.id === result.id);
          if (s && uniqueSpan(snapshot, s.text))
            next.push({
              text: s.text,
              source,
              key: fingerprint(
                source.before + "\0" + source.after + "\0" + s.text,
              ),
            });
        }
      }
      if (rev !== revision || !enabled || !snapshotValid) return;
      findings = next.map((f) => ({ ...f, suggestionState: "loading" }));
      error = "";
      publish();
      void generateSuggestions(findings, rev, snapshot);
    } catch (e) {
      if (rev === revision && enabled) {
        error = e.message;
        ui.results([]);
        ui.draw(new Map());
        state(e.retryable ? "Waiting for another check…" : "Could not check", {
          detail: error,
        });
        if (e.retryable) schedule(3000, true);
      }
    } finally {
      running = false;
      paint();
      if (enabled && rev !== revision) schedule();
    }
  }
  async function generateSuggestions(rows, rev, snapshot) {
    const groups = new Map();
    for (const row of rows) {
      if (!groups.has(row.source.id)) groups.set(row.source.id, []);
      groups.get(row.source.id).push(row);
    }
    for (const group of groups.values()) {
      for (let offset = 0; offset < group.length; offset += 4) {
        if (revision !== rev || !enabled || !snapshotValid) return;
        const batch = group
          .slice(offset, offset + 4)
          .filter((row) => findings.includes(row));
        if (!batch.length) continue;
        for (const row of batch) {
          row.suggestionState = "loading";
          row.suggestionError = "";
        }
        ui.results(visible);
        const source = batch[0].source;
        const passages = batch.map((row) => {
          const at = current.indexOf(row.text);
          return {
            id: row.key,
            text: row.text,
            context: current.slice(
              Math.max(0, at - 300),
              Math.min(current.length, at + row.text.length + 300),
            ),
          };
        });
        if (ui.root?.host)
          ui.root.host.dataset.draftRequests = String(
            Number(ui.root.host.dataset.draftRequests || 0) + 1,
          );
        const answer = await rpc({
          type: "suggest",
          input: {
            source: { before: source.before, after: source.after },
            passages,
          },
        });
        if (revision !== rev || !enabled || !snapshotValid) return;
        for (const row of batch) {
          const suggestion = answer.ok
            ? answer.suggestions?.find((s) => s.id === row.key)
            : null;
          row.suggestionState = suggestion ? "ready" : "error";
          row.suggestion = suggestion;
          row.suggestionError =
            answer.error ||
            "No suggestion was returned. You can edit the sentence directly.";
        }
        ui.results(visible);
      }
    }
  }
  async function applySuggestion(row, replacement, action = "replace") {
    if (activeApply)
      return { ok: false, error: "Another correction is being applied." };
    if (
      !enabled ||
      !snapshotValid ||
      current !== processed ||
      !visible.some((f) => f.key === row.key) ||
      !uniqueSpan(current, row.text)
    )
      return {
        ok: false,
        error: "This finding is stale. Wait for a fresh check.",
      };
    if (
      typeof replacement !== "string" ||
      !["replace", "delete"].includes(action) ||
      (action === "delete" ? replacement !== "" : !replacement.trim())
    )
      return { ok: false, error: "Invalid correction action." };
    if (replacement.length > 2500 || /[\r\n\u0000-\u001f]/.test(replacement))
      return {
        ok: false,
        error:
          "Use a single line of at most 2,500 characters for a correction.",
      };
    const requestId = crypto.randomUUID();
    const span = uniqueSpan(current, row.text);
    const transaction = {
      baseText: current,
      quote: row.text,
      replacement,
      span,
      revision,
      tab,
      snapshot: null,
    };
    activeApply = transaction;
    clearTimeout(timer);
    return new Promise((resolve) => {
      const finish = (result) => {
        clearTimeout(timeout);
        pendingApplies.delete(requestId);
        activeApply = null;
        // Only a bridge-confirmed, exact correction can advance the review baseline.
        // Keep the same review revision so other drafts can finish without rechecking.
        const unchanged =
          enabled &&
          snapshotValid &&
          revision === transaction.revision &&
          tab === transaction.tab &&
          current === transaction.baseText;
        if (
          result.ok &&
          unchanged &&
          rippleCorrection.matches(
            transaction.baseText,
            row.text,
            replacement,
            result.text,
          ) &&
          result.tab === transaction.tab
        ) {
          clearTimeout(timer);
          findings = findings.filter((f) => {
            const target = uniqueSpan(transaction.baseText, f.text);
            return (
              target &&
              (target.end <= span.start || target.start >= span.end) &&
              uniqueSpan(result.text, f.text) &&
              uniqueSpan(result.text, f.source.after)
            );
          });
          const sourcesBefore = [...sources];
          sources = sources.filter((s) => uniqueSpan(result.text, s.after));
          corrections.push({
            before: transaction.baseText,
            after: result.text,
            sourcesBefore,
            sourcesAfter: [...sources],
          });
          corrections = corrections.slice(-20);
          current = processed = result.text;
          error = "";
          publish();
          state(
            visible.length
              ? `${visible.length} ${visible.length === 1 ? "place" : "places"} may need updating`
              : "All suggestions reviewed",
            {
              announce:
                action === "delete" ? "Sentence removed." : "Change applied.",
            },
          );
        } else {
          if (result.ok)
            result = {
              ok: false,
              error:
                "The document changed during Apply. Wait for a fresh check.",
            };
          if (unchanged && transaction.snapshot)
            receiveSnapshot(transaction.snapshot);
        }
        resolve(result);
      };
      const timeout = setTimeout(
        () =>
          finish({
            ok: false,
            error:
              "Could not confirm the change. Check the Doc before trying again.",
          }),
        5000,
      );
      pendingApplies.set(requestId, finish);
      send({
        type: "apply",
        requestId,
        baseText: current,
        quote: row.text,
        replacement,
        action,
        tab,
      });
    });
  }
  window.addEventListener("message", (event) => {
    if (
      event.source !== window ||
      event.origin !== location.origin ||
      event.data?.channel !== channel
    )
      return;
    if (event.data.bridgeBuild && ui.root?.host)
      ui.root.host.dataset.bridgeBuild = event.data.bridgeBuild;
    if (event.data.type === "apply-result" && ui.root?.host)
      ui.root.host.dataset.lastApply = JSON.stringify({
        ok: event.data.ok,
        diagnostic: event.data.diagnostic,
      });
    if (event.data.type === "apply-result") {
      pendingApplies.get(event.data.requestId)?.(event.data);
      return;
    }
    if (event.data.type !== "snapshot" || !enabled) return;
    receiveSnapshot(event.data);
  });
  function receiveSnapshot(data) {
    if (data.error) {
      if (snapshotValid) revision++;
      snapshotValid = false;
      clearTimeout(timer);
      paintedRevision = -1;
      error = String(data.error).slice(0, 400);
      ui.results([]);
      ui.draw(new Map());
      state("Doc access unavailable");
      return;
    }
    if (typeof data.text !== "string" || data.text.length > 30000) return;
    // An in-flight read can arrive before the Apply acknowledgement. Hold only
    // its exact expected edit; any unrelated edit still invalidates this review.
    if (
      activeApply &&
      revision === activeApply.revision &&
      data.tab === activeApply.tab
    ) {
      if (data.text === activeApply.baseText) return;
      if (
        rippleCorrection.matches(
          activeApply.baseText,
          activeApply.quote,
          activeApply.replacement,
          data.text,
        )
      ) {
        activeApply.snapshot = data;
        return;
      }
    }
    const recovered = !snapshotValid;
    snapshotValid = true;
    if (!data.text.trim()) {
      clearTimeout(timer);
      revision++;
      paintedRevision = -1;
      current = "";
      processed = "";
      sources = [];
      corrections = [];
      findings = [];
      visible = [];
      error = "";
      starting = false;
      ui.results([]);
      ui.draw(new Map());
      ui.close();
      state("Ready for your next edit");
      return;
    }
    if (tab && tab !== data.tab) {
      reset();
      starting = true;
    }
    tab = data.tab;
    if (starting) {
      current = data.text;
      processed = data.text;
      starting = false;
      error = "";
      publish();
      return;
    }
    if (recovered && !starting && data.text === current) {
      error = "";
      schedule(1900, true);
    }
    if (data.text !== current) {
      current = data.text;
      revision++;
      paintedRevision = -1;
      ui.results([]);
      ui.draw(new Map());
      ui.close();
      state("Waiting for you to finish…");
      schedule();
    }
  }
  // Passive geometry uses Docs' labelled canvas rectangles. It never moves selection.
  const canvas = document.createElement("canvas"),
    context = canvas.getContext("2d");
  function collapse(s) {
    return s.replace(/\s+/g, " ").trim();
  }
  function geometry(quote) {
    const editor = document.querySelector(".kix-appview-editor");
    if (!editor) return [];
    const clip = editor.getBoundingClientRect();
    const seen = new Set();
    const parts = [...editor.querySelectorAll("rect[aria-label]")]
      .map((node) => ({
        node,
        text: collapse(node.getAttribute("aria-label") || ""),
        rect: node.getBoundingClientRect(),
      }))
      .filter((p) => {
        if (!p.text || !p.rect.width || !p.rect.height) return false;
        const key =
          p.text + ":" + Math.round(p.rect.left) + ":" + Math.round(p.rect.top);
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .sort((a, b) =>
        Math.abs(a.rect.top - b.rect.top) <
        Math.min(a.rect.height, b.rect.height) * 0.4
          ? a.rect.left - b.rect.left
          : a.rect.top - b.rect.top,
      );
    let stream = "";
    for (const p of parts) {
      if (stream) stream += " ";
      p.start = stream.length;
      stream += p.text;
      p.end = stream.length;
    }
    const q = collapse(quote),
      start = stream.indexOf(q);
    if (start < 0 || stream.indexOf(q, start + 1) >= 0) return [];
    const end = start + q.length,
      rects = [];
    for (const p of parts) {
      if (p.end <= start || p.start >= end) continue;
      const r = p.rect;
      if (
        r.top < Math.max(clip.top, 0) ||
        r.bottom > Math.min(clip.bottom, innerHeight) ||
        r.right < 0 ||
        r.left > innerWidth
      )
        continue;
      const a = Math.max(0, start - p.start),
        b = Math.min(p.text.length, end - p.start);
      let left = r.left,
        width = r.width;
      if (a > 0 || b < p.text.length) {
        const font = p.node.getAttribute("data-font-css");
        if (!font) continue; // Do not underline a guessed substring.
        context.font = font;
        const total = context.measureText(p.text).width;
        if (!total) continue;
        left +=
          (r.width * context.measureText(p.text.slice(0, a)).width) / total;
        width =
          (r.width *
            (context.measureText(p.text.slice(0, b)).width -
              context.measureText(p.text.slice(0, a)).width)) /
          total;
      }
      rects.push({
        left,
        right: left + width,
        top: r.top,
        bottom: r.bottom,
        width,
        height: r.height,
      });
    }
    return rects;
  }
  let frame = false;
  function paint() {
    if (frame) return;
    frame = true;
    requestAnimationFrame(() => {
      frame = false;
      const map = new Map();
      if (
        enabled &&
        snapshotValid &&
        !error &&
        !running &&
        paintedRevision === revision &&
        current === processed
      )
        for (const f of visible) map.set(f.key, geometry(f.text));
      ui.draw(map);
    });
  }
  setInterval(() => {
    if (visible.length) paint();
  }, 1000);
  document.addEventListener("scroll", paint, true);
  window.addEventListener("resize", paint);
  const observer = new MutationObserver((records) => {
    if (records.some((r) => !r.target.closest?.("#ripple-native"))) paint();
  });
  const editor = document.querySelector(".kix-appview-editor");
  if (editor)
    observer.observe(editor, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["style", "transform", "aria-label"],
    });
  function watchComposition(target) {
    target.addEventListener("compositionstart", () => {
      composing = true;
      clearTimeout(timer);
    });
    target.addEventListener("compositionend", () => {
      composing = false;
      schedule();
    });
  }
  watchComposition(document);
  try {
    const input = document.querySelector(
      ".docs-texteventtarget-iframe",
    )?.contentDocument;
    if (input) watchComposition(input);
  } catch {}
  chrome.runtime.onMessage.addListener((message, sender, respond) => {
    if (sender.id === chrome.runtime.id && message?.type === "toggle") {
      toggle(message.enabled);
      respond({ ok: true });
    }
  });
  const stored = await chrome.storage.local.get(storageKey);
  if (stored[storageKey]) toggle(true);
  else state("Enable Ripple");
})();
