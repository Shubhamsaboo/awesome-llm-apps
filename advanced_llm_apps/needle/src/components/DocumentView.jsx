import React from "react";
import { ShieldCheck, ArrowDown } from "lucide-react";
import Logo from "./Logo";
import { documents } from "../documents";
export default function DocumentView({
  doc,
  blocks,
  matches,
  selected,
  setActive,
  article,
}) {
  const matchMap = new Map(
    matches.map((match, index) => [match.id, { ...match, index }]),
  );
  function renderText(text, match) {
    if (!match) return text;
    const focus = match.focus;
    if (!focus || text.slice(focus.start, focus.end) !== focus.text)
      return <span className="meaning-highlight">{text}</span>;
    return (
      <span className="meaning-highlight">
        {text.slice(0, focus.start)}
        <mark className="sentence-highlight">{focus.text}</mark>
        {text.slice(focus.end)}
      </span>
    );
  }

  let blockIndex = 0;
  return (
    <section className="document-card">
      <div className="document-toolbar">
        <span>
          <span className="paper-dot" />
          {doc.id === "custom"
            ? "Your pasted document"
            : doc.publisher.toLowerCase().replaceAll(" ", "") + ".example"}
        </span>
        <span className="original-label">
          <ShieldCheck size={13} /> Original text
        </span>
      </div>
      <article ref={article} className="article">
        <div className="article-cover">
          <div className="cover-top">
            <span>{doc.tag}</span>
            <span>{doc.meta}</span>
          </div>
          <div className="cover-decoration" aria-hidden="true">
            <span />
            <span />
            <span />
            <div className="asterisk">✳</div>
          </div>
          <h2>
            {doc.title.split("\n").map((line, i) => (
              <React.Fragment key={i}>
                {line}
                {i === 0 && <br />}
              </React.Fragment>
            ))}
          </h2>
          <p>{doc.subtitle}</p>
          <div className="cover-bottom">
            <span>{doc.publisher}</span>
            <span>
              VOL. 0{documents.findIndex((d) => d.id === doc.id) + 1 || 4}{" "}
              <ArrowDown size={12} />
            </span>
          </div>
        </div>
        <div className="article-body">
          {doc.sections.map((s, si) => (
            <section key={s.heading}>
              <h3>
                <span>{String(si + 1).padStart(2, "0")}</span>
                {s.heading}
              </h3>
              {s.paragraphs.map((text) => {
                const id = `b${blockIndex++}`;
                const m = matchMap.get(id);
                return (
                  <p
                    id={`passage-${id}`}
                    key={id}
                    className={`passage ${m ? "matched" : ""} ${selected?.id === id ? "current" : ""}`}
                    onClick={() => {
                      if (m) setActive(m.index);
                    }}
                  >
                    {m && (
                      <button
                        className="passage-pin"
                        aria-label={`Select match ${m.index + 1}`}
                        onClick={() => setActive(m.index)}
                      >
                        {m.index + 1}
                      </button>
                    )}
                    {renderText(text, m)}
                  </p>
                );
              })}
            </section>
          ))}
          <div className="article-end">
            <Logo small />
            <span>You’ve reached the end. Find a new beginning.</span>
          </div>
        </div>
      </article>
      <div className="document-bottom">
        <span>
          {blocks.length} passages ·{" "}
          {blocks
            .reduce((n, b) => n + b.text.split(/\s+/).length, 0)
            .toLocaleString()}{" "}
          words
        </span>
        <span>
          {doc.id === "custom"
            ? "Your original text"
            : "Example content for exploring Needle"}
        </span>
      </div>
    </section>
  );
}
