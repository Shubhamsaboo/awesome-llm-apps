import Logo from "./components/Logo";
import DocumentView from "./components/DocumentView";
import ResultsPanel from "./components/ResultsPanel";
import Dialogs from "./components/Dialogs";
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  X,
  Search,
  ArrowUpRight,
  ArrowRight,
  Plus,
  FileText,
  Command,
  Sparkles,
  ChevronRight,
  BookOpen,
  PanelLeft,
  Chrome,
  Hotel,
  Utensils,
  MessagesSquare,
  LoaderCircle,
} from "lucide-react";
import { documents, getBlocks } from "./documents";
import { splitDocument } from "./search";
import "./style.css";
const icons = {
  stay: Hotel,
  recipe: Utensils,
  thread: MessagesSquare,
  custom: FileText,
};
export default function App() {
  const [doc, setDoc] = useState(documents[0]);
  const [query, setQuery] = useState("hidden fees");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState(0);
  const [modal, setModal] = useState(null);
  const [paste, setPaste] = useState("");
  const [pasteTitle, setPasteTitle] = useState("");
  const [custom, setCustom] = useState(null);
  const [copied, setCopied] = useState(false);
  const [sidebar, setSidebar] = useState(false);
  const [ready, setReady] = useState(null);
  const [token, setToken] = useState(
    () => sessionStorage.getItem("needle-token") || "",
  );
  const input = useRef(null),
    article = useRef(null),
    sequence = useRef(0),
    abort = useRef(null),
    cache = useRef(new Map()),
    timer = useRef(null),
    dialog = useRef(null);
  const blocks = useMemo(() => getBlocks(doc), [doc]);
  const matches = result?.matches || [];
  const selected = matches[active];
  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => setReady(d.configured))
      .catch(() => setReady(false));
  }, []);
  function invalidate() {
    sequence.current++;
    abort.current?.abort();
    clearTimeout(timer.current);
    setResult(null);
    setError("");
    setLoading(false);
    setActive(0);
  }
  async function runSearch() {
    clearTimeout(timer.current);
    const q = query.trim();
    const id = ++sequence.current;
    abort.current?.abort();
    setError("");
    setActive(0);
    if (q.length < 2) {
      setResult(null);
      setLoading(false);
      return;
    }
    const key = JSON.stringify([blocks, q, token]);
    if (cache.current.has(key)) {
      setResult({ ...cache.current.get(key), cached: true });
      setLoading(false);
      return;
    }
    setLoading(true);
    setResult(null);
    abort.current = new AbortController();
    try {
      const response = await fetch("/api/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "x-needle-token": token } : {}),
        },
        body: JSON.stringify({
          query: q,
          blocks: blocks.map(({ id, text }) => ({ id, text })),
        }),
        signal: abort.current.signal,
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.error || "Search failed. Please try again.");
      if (sequence.current !== id) return;
      if (cache.current.size >= 25)
        cache.current.delete(cache.current.keys().next().value);
      cache.current.set(key, data);
      setResult(data);
      setReady(true);
    } catch (e) {
      if (e.name !== "AbortError" && sequence.current === id)
        setError(e.message);
    } finally {
      if (sequence.current === id) setLoading(false);
    }
  }
  useEffect(() => {
    invalidate();
    timer.current = setTimeout(runSearch, 650);
    return () => clearTimeout(timer.current);
  }, [query, doc, token]);
  useEffect(() => () => abort.current?.abort(), []);
  useEffect(() => {
    if (!modal) return;
    const previous = document.activeElement;
    const root = dialog.current;
    const focusable = () => [
      ...root.querySelectorAll("button:not(:disabled),a,input,textarea"),
    ];
    focusable()[0]?.focus();
    function trap(e) {
      if (e.key !== "Tab") return;
      const items = focusable();
      if (e.shiftKey && document.activeElement === items[0]) {
        e.preventDefault();
        items.at(-1)?.focus();
      } else if (!e.shiftKey && document.activeElement === items.at(-1)) {
        e.preventDefault();
        items[0]?.focus();
      }
    }
    root.addEventListener("keydown", trap);
    return () => {
      root.removeEventListener("keydown", trap);
      previous?.focus();
    };
  }, [modal]);
  function move(delta) {
    if (matches.length)
      setActive((a) => (a + delta + matches.length) % matches.length);
  }
  useEffect(() => {
    if (selected) {
      const el = document.getElementById(`passage-${selected.id}`);
      if (el && article.current) {
        const container = article.current;
        const top =
          container.scrollTop +
          el.getBoundingClientRect().top -
          container.getBoundingClientRect().top -
          container.clientHeight / 2 +
          el.clientHeight / 2;
        container.scrollTo({
          top,
          behavior: window.matchMedia("(prefers-reduced-motion: reduce)")
            .matches
            ? "instant"
            : "smooth",
        });
      }
    }
  }, [selected?.id, result]);
  useEffect(() => {
    function key(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === "f") {
        e.preventDefault();
        input.current?.focus();
        input.current?.select();
      }
      if (e.key === "Escape") {
        setModal(null);
        input.current?.blur();
      }
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        move(e.shiftKey ? -1 : 1);
      }
    }
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [matches.length]);
  function chooseDoc(d) {
    invalidate();
    setDoc(d);
    setQuery(d.suggestions[0]);
    setSidebar(false);
    article.current?.scrollTo(0, 0);
  }
  async function copy() {
    const block = blocks.find((b) => b.id === selected?.id);
    if (!block) return;
    try {
      await navigator.clipboard.writeText(block.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setError("Could not copy. Select the passage text to copy it manually.");
    }
  }
  function addDoc() {
    const parsed = splitDocument(paste);
    if (!parsed.length) return;
    if (parsed.length > 160) {
      setError("Please use a shorter document with fewer than 160 passages.");
      return;
    }
    const d = {
      id: "custom",
      icon: "custom",
      name: pasteTitle.trim() || "Your document",
      kind: "Your own words",
      publisher: "YOUR READING SPACE",
      title: pasteTitle.trim() || "A fresh perspective.",
      subtitle: "Your original text. A better way to find your way through it.",
      tag: "PERSONAL DOCUMENT",
      meta: `${parsed.length} passages`,
      suggestions: [""],
      sections: [
        { heading: "The document", paragraphs: parsed.map((p) => p.text) },
      ],
    };
    setCustom(d);
    chooseDoc(d);
    setModal(null);
    setPaste("");
    setPasteTitle("");
    input.current?.focus();
  }
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <button
            className="mobile-menu icon-button"
            aria-label="Toggle library"
            onClick={() => setSidebar(!sidebar)}
          >
            <PanelLeft size={19} />
          </button>
          <Logo />
          <span className="brand-divider" />
          <span className="brand-caption">A little more understanding.</span>
        </div>
        <div className="top-actions">
          <span className="live-label">
            <span className={ready ? "live-dot" : "live-dot waiting"} />
            {ready
              ? "Powered by TypeSafe Jev"
              : ready === false
                ? "Jev needs setup"
                : "Connecting to Jev"}
          </span>
          <button
            className="extension-button"
            onClick={() => setModal("extension")}
          >
            <Chrome size={16} /> Get the extension <ArrowUpRight size={15} />
          </button>
        </div>
      </header>
      <div className="workspace">
        <aside className={`sidebar ${sidebar ? "open" : ""}`}>
          <div className="sidebar-intro">
            <span className="eyebrow">YOUR READING SPACE</span>
            <h2>
              Find the thought.
              <br />
              <span>Not just the words.</span>
            </h2>
          </div>
          <div className="library-title">
            <span>TRY A DOCUMENT</span>
            <span>{custom ? "04" : "03"}</span>
          </div>
          <nav className="documents">
            {[...documents, ...(custom ? [custom] : [])].map((d) => {
              const Icon = icons[d.icon];
              return (
                <button
                  key={d.id}
                  className={`doc-button ${doc.id === d.id ? "selected" : ""}`}
                  onClick={() => chooseDoc(d)}
                >
                  <span className="doc-icon">
                    <Icon size={18} />
                  </span>
                  <span>
                    <strong>{d.name}</strong>
                    <small>{d.kind}</small>
                  </span>
                  {doc.id === d.id && <span className="selection-dot" />}
                </button>
              );
            })}
          </nav>
          <button
            className="paste-button"
            onClick={() => {
              setError("");
              setModal("paste");
            }}
          >
            <Plus size={16} /> Bring your own text <span>↗</span>
          </button>
          <div className="sidebar-note">
            <div className="note-symbol">
              <Search size={17} />
              <Sparkles size={11} />
            </div>
            <p>
              You know what you’re
              <br />
              looking for.
              <br />
              <strong>
                You shouldn’t need
                <br />
                the exact words.
              </strong>
            </p>
            <span className="note-line" />
          </div>
          <div className="sidebar-bottom">
            <button onClick={() => setModal("about")}>
              <BookOpen size={14} /> How it works <ArrowUpRight size={13} />
            </button>
            <span>MADE FOR THE CURIOUS.</span>
          </div>
        </aside>
        <main>
          <div className="page-heading">
            <div className="breadcrumb">
              <span>Playground</span>
              <ChevronRight size={12} />
              <span>{doc.name}</span>
            </div>
            <button
              className="shortcut"
              onClick={() => {
                input.current?.focus();
                input.current?.select();
              }}
            >
              <Command size={12} /> F <span>to find anything</span>
            </button>
          </div>
          <section className="search-section">
            <div className="search-heading">
              <div>
                <div className="eyebrow">
                  <span className="tiny-star">✳</span> FIND WHAT YOU MEAN
                </div>
                <h1>
                  A new way to <span>find.</span>
                </h1>
              </div>
              <span className="search-hint">
                Your own words.
                <br />
                The right sentence.
              </span>
            </div>
            <form
              className={`search-dock ${loading ? "searching" : ""}`}
              onSubmit={(e) => {
                e.preventDefault();
                runSearch();
              }}
            >
              <Search className="search-glyph" size={22} />
              <input
                ref={input}
                aria-label="Search the document"
                placeholder="Describe what you’re looking for…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                maxLength={400}
              />
              {query && (
                <button
                  type="button"
                  className="clear-button"
                  aria-label="Clear search"
                  onClick={() => setQuery("")}
                >
                  <X size={15} />
                </button>
              )}
              <button className="submit-button" aria-label="Run search">
                {loading ? (
                  <LoaderCircle size={20} className="spin" />
                ) : (
                  <ArrowRight size={20} />
                )}
              </button>
            </form>
            <div className="suggestions">
              <span>Try a thought</span>
              {doc.suggestions.filter(Boolean).map((q) => (
                <button
                  key={q}
                  className={query === q ? "chosen" : ""}
                  onClick={() => {
                    setQuery(q);
                  }}
                >
                  {q}
                  <ArrowUpRight size={11} />
                </button>
              ))}
            </div>
          </section>
          <div className="reading-grid">
            <DocumentView
              doc={doc}
              blocks={blocks}
              matches={matches}
              selected={selected}
              setActive={setActive}
              article={article}
            />
            <ResultsPanel
              loading={loading}
              error={error}
              result={result}
              matches={matches}
              active={active}
              blocks={blocks}
              copied={copied}
              runSearch={runSearch}
              move={move}
              setActive={setActive}
              copy={copy}
            />
          </div>
          <footer className="main-footer">
            <span>LESS HUNTING. MORE FINDING.</span>
            <span>
              Powered by <strong>TypeSafe Jev</strong>
            </span>
          </footer>
        </main>
      </div>
      <Dialogs
        modal={modal}
        dialog={dialog}
        setModal={setModal}
        paste={paste}
        setPaste={setPaste}
        pasteTitle={pasteTitle}
        setPasteTitle={setPasteTitle}
        error={error}
        addDoc={addDoc}
        token={token}
        setToken={setToken}
      />
    </div>
  );
}
