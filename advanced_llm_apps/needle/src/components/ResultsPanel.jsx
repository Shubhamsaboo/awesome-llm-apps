import React from "react";
import {
  Sparkles,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  ArrowUpRight,
  Check,
  Copy,
  MousePointer2,
} from "lucide-react";
export default function ResultsPanel({
  loading,
  error,
  result,
  matches,
  active,
  blocks,
  copied,
  runSearch,
  move,
  setActive,
  copy,
}) {
  return (
    <aside className="results-panel">
      <div className="results-top">
        <span className="eyebrow">THE GOOD PARTS</span>
        <span className="results-icon">
          <Sparkles size={17} />
        </span>
      </div>
      <div className="result-summary" aria-live="polite">
        {loading ? (
          <>
            <h2>
              Reading between
              <br />
              the lines<span className="dots">...</span>
            </h2>
            <p>Finding passages that speak to your search.</p>
          </>
        ) : error ? (
          <>
            <h2>
              A small
              <br />
              interruption.
            </h2>
            <p className="error-text">{error}</p>
            <button className="retry-button" onClick={runSearch}>
              Try again <ArrowRight size={14} />
            </button>
          </>
        ) : result ? (
          <>
            <h2>
              {matches.length ? (
                <>
                  <span className="count">{matches.length}</span>{" "}
                  {matches.length === 1 ? "connection" : "connections"}
                  <br />
                  worth a look.
                </>
              ) : (
                <>
                  No strong
                  <br />
                  matches.
                </>
              )}
            </h2>
            <p>
              {matches.length
                ? "The key sentence, with the surrounding context."
                : "Try a different question or add a little more context."}
            </p>
          </>
        ) : (
          <>
            <h2>
              Follow your
              <br />
              curiosity.
            </h2>
            <p>Describe a thought. We’ll find where it lives in the text.</p>
          </>
        )}
      </div>
      {loading && (
        <div className="skeleton-stack">
          {[1, 2, 3].map((i) => (
            <div className="skeleton" key={i}>
              <span />
              <span />
              <span />
            </div>
          ))}
        </div>
      )}
      {!loading && !error && matches.length > 0 && (
        <>
          <div className="match-navigation">
            <span>
              {active + 1} <span>/ {matches.length}</span>
            </span>
            <div>
              <button aria-label="Previous match" onClick={() => move(-1)}>
                <ArrowUp size={14} />
              </button>
              <button aria-label="Next match" onClick={() => move(1)}>
                <ArrowDown size={14} />
              </button>
            </div>
          </div>
          <div className="matches-list">
            {matches.map((m, i) => {
              const b = blocks.find((b) => b.id === m.id);
              return (
                <button
                  key={m.id}
                  className={`match-card ${i === active ? "active" : ""}`}
                  onClick={() => setActive(i)}
                >
                  <div className="match-card-heading">
                    <span className="match-number">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span>{b.heading}</span>
                    <ArrowUpRight size={13} />
                  </div>
                  <p>{m.focus?.text || b.text}</p>
                  <span className="match-card-foot">
                    {m.probability >= 0.85
                      ? "Strong connection"
                      : "Related passage"}
                    <span>{i === active ? "IN VIEW" : "JUMP TO TEXT"}</span>
                  </span>
                </button>
              );
            })}
          </div>
          <button className="copy-button" onClick={copy}>
            {copied ? <Check size={14} /> : <Copy size={14} />}{" "}
            {copied ? "Copied original passage" : "Copy selected passage"}
          </button>
        </>
      )}
      <div className="results-bottom">
        {result && (
          <div className="timing">
            <span className="live-dot" />
            <span>
              {result.elapsedMs.toLocaleString()} ms{" "}
              <span>· {result.cached ? "saved result" : "TypeSafe Jev"}</span>
            </span>
          </div>
        )}
        <p>
          <MousePointer2 size={12} /> Brighter highlight = key sentence. Pale
          highlight = context.
        </p>
      </div>
    </aside>
  );
}
