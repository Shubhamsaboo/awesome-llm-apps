import React from "react";
import {
  X,
  ArrowRight,
  Chrome,
  ArrowUpRight,
  Search,
  FileText,
} from "lucide-react";
import Logo from "./Logo";
export default function Dialogs({
  modal,
  dialog,
  setModal,
  paste,
  setPaste,
  pasteTitle,
  setPasteTitle,
  error,
  addDoc,
  token,
  setToken,
}) {
  if (!modal) return null;
  return (
    <div className="modal-backdrop" onClick={() => setModal(null)}>
      <section
        ref={dialog}
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={
          modal === "paste"
            ? "Add your text"
            : modal === "extension"
              ? "Install Needle extension"
              : "About Needle"
        }
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="modal-close icon-button"
          aria-label="Close dialog"
          onClick={() => setModal(null)}
        >
          <X size={20} />
        </button>
        <Logo />
        {modal === "paste" ? (
          <>
            <h2>
              Your text.
              <br />
              <em>A fresh set of eyes.</em>
            </h2>
            <p>
              Paste an article, a conversation, or the fine print. Search sends
              this text to Jev through AI Gateway.
            </p>
            <label>
              DOCUMENT NAME
              <input
                value={pasteTitle}
                onChange={(e) => setPasteTitle(e.target.value)}
                placeholder="Something worth reading"
                maxLength={100}
              />
            </label>
            <label>
              THE ORIGINAL TEXT
              <textarea
                value={paste}
                onChange={(e) => setPaste(e.target.value)}
                placeholder="Paste your text here…"
                maxLength={60000}
              />
            </label>
            <div className="modal-foot">
              <span>{paste.length.toLocaleString()} / 60,000 characters</span>
              <button
                disabled={!paste.trim()}
                className="primary"
                onClick={addDoc}
              >
                Start exploring <ArrowRight size={16} />
              </button>
            </div>
            {error && <p className="error-text">{error}</p>}
          </>
        ) : modal === "extension" ? (
          <>
            <h2>
              A new way to find.
              <br />
              <em>On your own pages.</em>
            </h2>
            <p>
              Bring Needle to Chrome. Search the text on a page with a floating
              search bar and jump directly to the source.
            </p>
            <ol className="steps">
              <li>
                <strong>Download & unzip</strong>
                <span>
                  Keep the unzipped folder in a permanent location. It must
                  contain manifest.json.
                </span>
              </li>
              <li>
                <strong>Load it in Chrome</strong>
                <span>
                  Open chrome://extensions, enable Developer mode, then “Load
                  unpacked”. Choose the unzipped folder containing
                  manifest.json.
                </span>
              </li>
              <li>
                <strong>Connect & explore</strong>
                <span>
                  In extension settings, use <code>{location.origin}</code> as
                  the server. Click the Needle icon on any normal webpage, or
                  press Cmd+Shift+F on Mac or Ctrl+Shift+F on Windows/Linux.
                  Leave the access token blank for local setup.
                </span>
              </li>
            </ol>
            <a
              className="primary download"
              href="/needle-extension.zip"
              download
            >
              <Chrome size={17} /> Download Chrome extension{" "}
              <ArrowUpRight size={16} />
            </a>
            <small className="modal-small">
              Your Needle backend must stay reachable. Your AI Gateway key stays
              on the server. Meaning search sends the page’s readable passages
              and your query for evaluation.
            </small>
          </>
        ) : (
          <>
            <h2>
              A search bar
              <br />
              <em>with a little intuition.</em>
            </h2>
            <p>
              Describe what you’re looking for. Jev finds relevant passages and
              picks the strongest sentence in each. A brighter highlight shows
              that sentence; a softer highlight keeps its context visible.
            </p>
            <div className="about-grid">
              <div>
                <Search size={20} />
                <strong>Find the idea</strong>
                <span>Paraphrases, synonyms, and relevant answers.</span>
              </div>
              <div>
                <FileText size={20} />
                <strong>Stay at the source</strong>
                <span>Original passages. No invented summaries.</span>
              </div>
            </div>
            <p>
              Relevance is a model judgment, not a guarantee. Read the
              highlighted passage in context. Your text isn’t saved on our
              server.
            </p>
            <label>
              SERVER ACCESS TOKEN <span>(optional)</span>
              <input
                type="password"
                value={token}
                onChange={(e) => {
                  setToken(e.target.value);
                  sessionStorage.setItem("needle-token", e.target.value);
                }}
                placeholder="Only for a protected deployment"
              />
            </label>
            <button className="primary" onClick={() => setModal(null)}>
              Let’s find something <ArrowRight size={16} />
            </button>
          </>
        )}
      </section>
    </div>
  );
}
