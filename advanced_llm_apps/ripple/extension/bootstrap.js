// Use Ripple's own identity. Never impersonate another extension.
if (!window._docs_annotate_canvas_by_ext)
  window._docs_annotate_canvas_by_ext = "fmalimpikdmpeejecilonpfjklejiccd";
// Text bridge. Selection and document changes require explicit navigation or Apply.
(() => {
  let enabled = false,
    busy = false,
    applying = false,
    enableEpoch = 0,
    readEpoch = 0;
  const channel = "ripple-docs-v1";
  const reply = (payload) =>
    window.postMessage(
      { channel, bridgeBuild: "review-continuity-4", ...payload },
      location.origin,
    );
  const textOf = (raw) =>
    String(raw ?? "")
      .replace(/^\u0003/, "")
      .replace(/\n$/, "");
  async function read() {
    if (!enabled || busy || applying || document.hidden) return;
    busy = true;
    const epoch = readEpoch,
      enabledAt = enableEpoch;
    try {
      if (typeof window._docs_annotate_getAnnotatedText !== "function") {
        reply({
          type: "snapshot",
          error:
            "Google Docs has not exposed its text adapter. Reload this Doc once. If it persists, this Docs version is not supported yet.",
        });
        return;
      }
      const api = await window._docs_annotate_getAnnotatedText();
      if (
        applying ||
        !enabled ||
        epoch !== readEpoch ||
        enabledAt !== enableEpoch
      )
        return;
      const text = textOf(api?.getText?.());
      if (text.length > 30000)
        reply({
          type: "snapshot",
          error:
            "This prototype supports documents up to 30,000 characters. Nothing was sent.",
        });
      else
        reply({
          type: "snapshot",
          text,
          tab: new URL(location.href).searchParams.get("tab") || "default",
        });
    } catch {
      reply({
        type: "snapshot",
        error:
          "Google Docs text could not be read. Reload the Doc and try again.",
      });
    } finally {
      busy = false;
    }
  }
  window.addEventListener("message", async (event) => {
    if (
      event.source !== window ||
      event.origin !== location.origin ||
      event.data?.channel !== channel
    )
      return;
    if (event.data.type === "enabled") {
      enableEpoch++;
      enabled = event.data.enabled === true;
      if (enabled) read();
    }
    if (event.data.type === "apply" && enabled) {
      const request = event.data;
      const respond = (ok, error = "", text, diagnostic) =>
        reply({
          type: "apply-result",
          requestId: request.requestId,
          ok,
          error,
          diagnostic,
          ...(ok ? { text, tab: request.tab } : {}),
        });
      if (applying) {
        respond(false, "Another correction is being applied.");
        return;
      }
      const deleting = request.action === "delete";
      if (
        typeof request.replacement !== "string" ||
        !["replace", "delete"].includes(request.action) ||
        (deleting
          ? request.replacement !== ""
          : !request.replacement?.trim()) ||
        typeof request.requestId !== "string" ||
        typeof request.baseText !== "string" ||
        request.baseText.length > 30000 ||
        typeof request.quote !== "string" ||
        !request.quote ||
        request.quote.length > 2500 ||
        typeof request.replacement !== "string" ||
        request.replacement.length > 2500 ||
        /[\r\n\u0000-\u001f]/.test(request.replacement)
      ) {
        respond(false, "Invalid correction.");
        return;
      }
      if (
        (new URL(location.href).searchParams.get("tab") || "default") !==
        request.tab
      ) {
        respond(false, "The document tab changed. Please recheck.");
        return;
      }
      applying = true;
      readEpoch++;
      const applyEpoch = enableEpoch;
      try {
        const api = await window._docs_annotate_getAnnotatedText();
        if (
          !enabled ||
          applyEpoch !== enableEpoch ||
          (new URL(location.href).searchParams.get("tab") || "default") !==
            request.tab
        ) {
          respond(
            false,
            "Ripple was paused or the document tab changed. Nothing was applied.",
          );
          return;
        }
        const raw = String(api.getText());
        if (textOf(raw) !== request.baseText) {
          respond(
            false,
            "The document changed. Wait for Ripple to recheck before applying.",
          );
          return;
        }
        const start = raw.indexOf(request.quote);
        if (start < 0 || raw.indexOf(request.quote, start + 1) >= 0) {
          respond(
            false,
            "This sentence is no longer uniquely located. Edit it directly.",
          );
          return;
        }
        const iframe = document.querySelector(".docs-texteventtarget-iframe");
        const targetDocument = iframe?.contentDocument;
        if (!targetDocument || typeof api.setSelection !== "function") {
          respond(
            false,
            "Direct editing is unavailable in this Docs version. Nothing was applied.",
          );
          return;
        }
        // activeElement can be BODY after a click on Ripple. Find the actual editor instead.
        const target =
          targetDocument.querySelector('[contenteditable="true"]') ||
          (targetDocument.activeElement?.isContentEditable
            ? targetDocument.activeElement
            : null);
        if (!target) {
          respond(
            false,
            "Google Docs editing input is unavailable. Check that the Doc is in Editing mode.",
          );
          return;
        }
        iframe.contentWindow?.focus();
        target.focus({ preventScroll: true });
        await api.setSelection(start, start + request.quote.length);
        // Let Docs commit its selection, then revalidate after the asynchronous boundary.
        await new Promise((resolve) => setTimeout(resolve, 0));
        const selected = await window._docs_annotate_getAnnotatedText();
        if (
          !enabled ||
          applyEpoch !== enableEpoch ||
          (new URL(location.href).searchParams.get("tab") || "default") !==
            request.tab
        ) {
          respond(
            false,
            "Ripple was paused or the document tab changed. Nothing was applied.",
          );
          return;
        }
        if (String(selected.getText()) !== raw) {
          respond(
            false,
            "The document changed before applying. Wait for a fresh check.",
          );
          return;
        }
        if (targetDocument.activeElement !== target) {
          respond(
            false,
            "Google Docs lost editing focus. Nothing was applied.",
          );
          return;
        }
        const selection = selected.getSelection?.()?.[0];
        if (selection) {
          for (const [a, b] of [
            ["anchor", "focus"],
            ["base", "extent"],
            ["start", "end"],
          ]) {
            if (
              typeof selection[a] !== "number" ||
              typeof selection[b] !== "number"
            )
              continue;
            if (
              Math.min(selection[a], selection[b]) !== start ||
              Math.max(selection[a], selection[b]) !==
                start + request.quote.length
            ) {
              respond(false, "The selected text changed. Nothing was applied.");
              return;
            }
            break;
          }
        }
        // Docs owns the text model. Its iframe is an event sink, not the document DOM.
        // Send one input operation to Docs' handlers instead of editing the proxy div.
        const realm = targetDocument.defaultView;
        if (deleting) {
          const options = {
            key: "Backspace",
            code: "Backspace",
            keyCode: 8,
            which: 8,
            bubbles: true,
            cancelable: true,
            composed: true,
            view: realm,
          };
          target.dispatchEvent(new realm.KeyboardEvent("keydown", options));
          target.dispatchEvent(new realm.KeyboardEvent("keyup", options));
        } else {
          const data = new realm.DataTransfer();
          data.setData("text/plain", request.replacement);
          target.dispatchEvent(
            new realm.ClipboardEvent("paste", {
              clipboardData: data,
              bubbles: true,
              cancelable: true,
              composed: true,
            }),
          );
        }
        for (let attempt = 0; attempt < 20; attempt++) {
          await new Promise((resolve) => setTimeout(resolve, 80));
          const latest = await window._docs_annotate_getAnnotatedText();
          const text = textOf(latest.getText());
          if (
            rippleCorrection.matches(
              request.baseText,
              request.quote,
              request.replacement,
              text,
            )
          ) {
            respond(true, "", text);
            return;
          }
          if (text !== request.baseText) {
            const at = request.baseText.indexOf(request.quote),
              expected =
                request.baseText.slice(0, at) +
                request.replacement +
                request.baseText.slice(at + request.quote.length);
            let first = 0;
            while (
              first < Math.min(text.length, expected.length) &&
              text[first] === expected[first]
            )
              first++;
            respond(
              false,
              "The Doc changed, but not exactly as expected. Check it before making another edit.",
              undefined,
              {
                offsetFromEdit: first - at,
                lengthDifference: text.length - expected.length,
                expectedCodes: [...expected.slice(first, first + 8)].map((c) =>
                  c.codePointAt(0),
                ),
                actualCodes: [...text.slice(first, first + 8)].map((c) =>
                  c.codePointAt(0),
                ),
              },
            );
            return;
          }
        }
        respond(
          false,
          "Google Docs did not confirm the edit. Nothing was retried. Check the selected sentence before editing manually.",
        );
      } catch {
        respond(
          false,
          "Could not confirm the correction. Check the Doc before retrying.",
        );
      } finally {
        applying = false;
        read();
      }
      return;
    }
    if (event.data.type === "navigate" && enabled && !applying) {
      // Quote validation avoids selecting the wrong text after a concurrent edit.
      const quote = event.data.quote;
      if (typeof quote !== "string" || quote.length > 3000) return;
      try {
        const api = await window._docs_annotate_getAnnotatedText();
        const raw = String(api.getText());
        const start = raw.indexOf(quote);
        if (
          start >= 0 &&
          raw.indexOf(quote, start + 1) < 0 &&
          typeof api.setSelection === "function"
        )
          api.setSelection(start, start + quote.length);
      } catch {}
    }
  });
  setInterval(read, 600);
})();
