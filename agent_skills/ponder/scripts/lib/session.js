// Session state: where a pondering lives on disk, how it is loaded, saved, and advanced.
//
// Layout (SPEC 3):
//   .ponder/<slug>/session.json  units.json  findings.json  ledger.jsonl  passes/NN/...
//
// Sessions live under <project>/.ponder/ when that directory is writable, and under
// ~/.ponder/ when it is not. PONDER_HOME overrides the home fallback (the conformance
// suite uses it to stay hermetic).

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

export const STATE_VERSION = 1;

/** The legal per-pass cycle. `session.phase` always names one of these. */
export const PHASES = ['predict', 'survey', 'appraise', 'deliberate', 'revise', 'judge', 'decide'];
export const SESSION_STATUSES = ['open', 'converged', 'stopped', 'aborted', 'applied'];

/** An error the user can act on. `code` is the process exit code: 1 user, 2 state machine. */
export class PonderError extends Error {
  constructor(message, code = 1, detail = []) {
    super(message);
    this.name = 'PonderError';
    this.code = code;
    this.detail = Array.isArray(detail) ? detail : [detail];
  }
}

export const userError = (message, detail) => new PonderError(message, 1, detail);
export const stateError = (message, detail) => new PonderError(message, 2, detail);

// ---------------------------------------------------------------------------
// paths
// ---------------------------------------------------------------------------

export function homeDir() {
  return process.env.PONDER_HOME && process.env.PONDER_HOME.trim() !== ''
    ? path.resolve(process.env.PONDER_HOME)
    : os.homedir();
}

/**
 * What a project root looks like.
 *
 * These are the files and directories that mean "the thing above me is a project": a
 * version-control root, or the manifest a toolchain reads to know what it is building.
 * Order matters only for reporting — the first match at a directory is the one named as
 * the reason — so the strongest signals come first.
 *
 * `.ponder` is deliberately NOT in this list. It is where a project's sessions are kept,
 * not what makes something a project, and it must never outrank the thing it belongs to.
 * See `resolveProjectRoot`.
 */
export const PROJECT_MARKERS = [
  '.git',
  '.hg',
  '.svn',
  'package.json',
  'go.mod',
  'Cargo.toml',
  'pyproject.toml',
  'deno.json',
  'deno.jsonc',
  'Gemfile',
  'pom.xml',
  'build.gradle',
  'build.gradle.kts',
  'composer.json',
  'mix.exs',
];

/** Suffix markers — a project root named by extension rather than by filename. */
export const PROJECT_MARKER_SUFFIXES = ['.xcodeproj', '.xcworkspace'];

/** How a project root was arrived at. `projectRootIsGuessed` says which of these to trust. */
export const PROJECT_ORIGINS = ['explicit', 'marker', 'ponder', 'cwd'];

/** The project marker present in `dir`, or null. Literal names first, then the suffixes. */
export function projectMarkerAt(dir) {
  for (const marker of PROJECT_MARKERS) {
    if (fs.existsSync(path.join(dir, marker))) return marker;
  }
  // Only worth a readdir when no literal marker matched: an Xcode project is a directory
  // whose *name* is the marker, so there is nothing to stat for.
  let entries;
  try {
    entries = fs.readdirSync(dir);
  } catch {
    return null;
  }
  for (const entry of entries) {
    for (const suffix of PROJECT_MARKER_SUFFIXES) {
      if (entry.length > suffix.length && entry.endsWith(suffix)) return entry;
    }
  }
  return null;
}

/**
 * Where the project being pondered actually is, and how that was decided.
 *
 * Two walks, and the ordering is the whole point.
 *
 * 1. Up the tree for a real project marker (`.git`, `package.json`, …). A hit is the
 *    project root, full stop — `.git` defines what the project IS.
 * 2. Only when no marker exists anywhere up the tree, up the tree again for an existing
 *    `.ponder`. With no project to anchor to, adopting a session store that is already
 *    there is the most useful thing available — but it is a guess, and it is recorded and
 *    reported as one.
 * 3. Otherwise the working directory.
 *
 * One walk over both kinds of marker is what let an unrelated ancestor `.ponder` silently
 * capture a directory that had no markers of its own: every relative path in the session
 * then resolved against a root the user never chose, and a path that "does not exist" under
 * a wrong root is not evidence of anything. `how` is what lets the phantom check (SPEC 3.5)
 * tell a checked absence from a guess.
 *
 * Returns `{ root, how, marker, cwd }`.
 */
export function resolveProjectRoot(cwd = process.cwd()) {
  const from = path.resolve(cwd);

  let dir = from;
  for (;;) {
    const marker = projectMarkerAt(dir);
    if (marker) return { root: dir, how: 'marker', marker, cwd: from };
    const up = path.dirname(dir);
    if (up === dir) break;
    dir = up;
  }

  dir = from;
  for (;;) {
    if (fs.existsSync(path.join(dir, '.ponder'))) return { root: dir, how: 'ponder', marker: '.ponder', cwd: from };
    const up = path.dirname(dir);
    if (up === dir) break;
    dir = up;
  }

  return { root: from, how: 'cwd', marker: null, cwd: from };
}

/** The project root alone. Every command that does not care how it was decided uses this. */
export function findProjectRoot(cwd = process.cwd()) {
  return resolveProjectRoot(cwd).root;
}

/**
 * True when the root was found rather than established — no project marker decided it.
 *
 * A guessed root makes every relative path in the session a guess too, so an absent file
 * says "we may be looking in the wrong place", not "the screen does not exist" (SPEC 3.5).
 */
export function projectRootIsGuessed(how) {
  return how === 'ponder' || how === 'cwd';
}

/** One clause saying why this directory is the project root. */
export function describeProjectOrigin({ how, marker, root, cwd } = {}) {
  switch (how) {
    case 'explicit':
      return 'given with --project';
    case 'marker':
      return `matched ${marker}`;
    case 'ponder':
      return root && cwd && root !== cwd
        ? 'no project marker anywhere above the working directory; adopted an ancestor .ponder'
        : 'no project marker here; adopted the .ponder already in this directory';
    case 'cwd':
      return 'no project marker anywhere above the working directory; fell back to it';
    default:
      return 'recorded before ponder tracked how the root was decided';
  }
}

/**
 * How an existing session's root was decided.
 *
 * Sessions written before `projectFrom` existed do not carry it, and they must not be
 * refused or nagged retroactively. For those, the origin is re-derived from the recorded
 * root itself — a root that holds a project marker was a sound root however it was found,
 * and one that does not was a guess. That is a fact about the recorded path, not about
 * wherever the current command happens to be running.
 */
export function projectOriginOf(session) {
  const root = session && typeof session.project === 'string' ? session.project : null;
  const from = session && session.projectFrom;
  if (from && typeof from === 'object' && PROJECT_ORIGINS.includes(from.how)) {
    return { root, how: from.how, marker: from.marker || null, cwd: from.cwd || null, recorded: true };
  }
  if (!root) return { root, how: 'cwd', marker: null, cwd: null, recorded: false };
  const marker = projectMarkerAt(root);
  return marker
    ? { root, how: 'marker', marker, cwd: null, recorded: false }
    : { root, how: 'cwd', marker: null, cwd: null, recorded: false };
}

/** Every store root that may hold sessions, project first. */
export function storeRoots(project = findProjectRoot()) {
  const roots = [path.join(project, '.ponder'), path.join(homeDir(), '.ponder')];
  return [...new Set(roots)];
}

/** Pick (and create) the store root for a new session: project when writable, else home. */
export function ensureStoreRoot(project) {
  const projectStore = path.join(project, '.ponder');
  try {
    fs.mkdirSync(projectStore, { recursive: true });
    fs.accessSync(projectStore, fs.constants.W_OK);
    return projectStore;
  } catch {
    const homeStore = path.join(homeDir(), '.ponder');
    try {
      fs.mkdirSync(homeStore, { recursive: true });
      return homeStore;
    } catch (err) {
      throw userError(
        `cannot create a session store — ${projectStore} is not writable and neither is ${homeStore} (${err.code || err.message}).`,
      );
    }
  }
}

export const sessionPaths = (dir) => ({
  dir,
  session: path.join(dir, 'session.json'),
  units: path.join(dir, 'units.json'),
  findings: path.join(dir, 'findings.json'),
  ledger: path.join(dir, 'ledger.jsonl'),
  passes: path.join(dir, 'passes'),
  report: path.join(dir, 'report.md'),
  applyPlan: path.join(dir, 'apply-plan.md'),
  ocaLog: path.join(dir, 'oca.log'),
});

/** passes/NN, created on demand. */
export function passDir(dir, pass, { create = true } = {}) {
  const p = path.join(dir, 'passes', String(pass).padStart(2, '0'));
  if (create) fs.mkdirSync(p, { recursive: true });
  return p;
}

export function passFile(dir, pass, name, { create = false } = {}) {
  return path.join(passDir(dir, pass, { create }), name);
}

// ---------------------------------------------------------------------------
// io
// ---------------------------------------------------------------------------

export function readJSON(file, { label = null, optional = false } = {}) {
  let text;
  try {
    text = fs.readFileSync(file, 'utf8');
  } catch (err) {
    if (optional && err.code === 'ENOENT') return null;
    if (err.code === 'ENOENT') throw userError(`${label || 'file'} not found: ${file}`);
    throw userError(`cannot read ${label || 'file'} ${file}: ${err.code || err.message}`);
  }
  try {
    return JSON.parse(text);
  } catch (err) {
    throw userError(`${label || file} is not valid JSON: ${err.message}`);
  }
}

/** Write JSON atomically — a half-written session.json is a corrupt session. */
export function writeJSON(file, value) {
  const tmp = `${file}.tmp-${process.pid}`;
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(tmp, JSON.stringify(value, null, 2) + '\n', 'utf8');
    fs.renameSync(tmp, file);
  } catch (err) {
    try {
      fs.unlinkSync(tmp);
    } catch {
      /* the temp file may not exist */
    }
    throw userError(`cannot write ${file}: ${err.code || err.message}`);
  }
}

export function readText(file, { optional = false } = {}) {
  try {
    return fs.readFileSync(file, 'utf8');
  } catch (err) {
    if (optional && err.code === 'ENOENT') return null;
    throw userError(`cannot read ${file}: ${err.code || err.message}`);
  }
}

export function writeText(file, text) {
  const tmp = `${file}.tmp-${process.pid}`;
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(tmp, text, 'utf8');
    fs.renameSync(tmp, file);
  } catch (err) {
    try {
      fs.unlinkSync(tmp);
    } catch {
      /* the temp file may not exist */
    }
    throw userError(`cannot write ${file}: ${err.code || err.message}`);
  }
}

/** Append JSONL records. Never rewrites; the ledger is append-only forever (SPEC 8.2). */
export function appendJSONL(file, records) {
  if (!records || records.length === 0) return;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.appendFileSync(file, records.map((r) => JSON.stringify(r)).join('\n') + '\n', 'utf8');
}

/**
 * Read JSONL.
 *
 * `tolerant` is for the append-only records the engine owns (the ledger, a pass's
 * deltas.jsonl). One line mangled by a crash mid-append must not permanently brick judge,
 * report and therefore the whole session — the surviving lines are still the truth. Bad
 * lines are pushed onto `skipped` so the caller can say out loud that it happened.
 * User-supplied payloads stay strict: there, a bad line is a bad batch.
 */
export function readJSONL(file, { label = null, tolerant = false, skipped = null } = {}) {
  let text;
  try {
    text = fs.readFileSync(file, 'utf8');
  } catch (err) {
    if (err.code === 'ENOENT') return [];
    throw userError(`cannot read ${label || file}: ${err.code || err.message}`);
  }
  const out = [];
  const lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line === '') continue;
    try {
      out.push(JSON.parse(line));
    } catch (err) {
      if (tolerant) {
        if (skipped) skipped.push({ file, line: i + 1, text: line.slice(0, 120), error: err.message });
        continue;
      }
      throw userError(`${label || file} line ${i + 1} is not valid JSON: ${err.message}`);
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// slugs
// ---------------------------------------------------------------------------

const STOPWORDS = new Set(['the', 'a', 'an', 'our', 'my', 'its', 'this', 'these', 'their', 'your']);

export function slugifySubject(subject) {
  const words = String(subject || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  while (words.length > 1 && STOPWORDS.has(words[0])) words.shift();
  const slug = words.join('-').slice(0, 40).replace(/-+$/, '');
  return slug;
}

export function today(date = new Date()) {
  return date.toISOString().slice(0, 10);
}

/** `<subject>-<YYYY-MM-DD>`, deduped with a numeric suffix when the directory exists. */
export function generateSlug(subject, lens, root, date = new Date()) {
  const base = `${slugifySubject(subject) || String(lens || 'ponder')}-${today(date)}`;
  let slug = base;
  let n = 2;
  while (fs.existsSync(path.join(root, slug))) slug = `${base}-${n++}`;
  return slug;
}

export function validateSlug(slug) {
  if (!/^[a-z0-9][a-z0-9._-]*$/.test(slug)) {
    throw userError(
      `slug "${slug}" is not usable — use lowercase letters, digits, dot, dash and underscore, starting with a letter or digit.`,
    );
  }
  return slug;
}

// ---------------------------------------------------------------------------
// discovery
// ---------------------------------------------------------------------------

/**
 * Every session on disk, newest first.
 *
 * A directory whose session.json cannot be read is skipped rather than fatal — one corrupt
 * session must not take out `ponder list`. It is pushed onto `broken` instead, because a
 * session that silently disappears from the listing is how an agent ends up starting a
 * second pondering of the same subject and losing the first.
 */
export function listSessions({ project = findProjectRoot(), broken = null } = {}) {
  const found = [];
  for (const root of storeRoots(project)) {
    let entries;
    try {
      entries = fs.readdirSync(root, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const dir = path.join(root, entry.name);
      const file = path.join(dir, 'session.json');
      if (!fs.existsSync(file)) continue;
      let session;
      try {
        session = JSON.parse(fs.readFileSync(file, 'utf8'));
        if (!session || typeof session !== 'object' || Array.isArray(session)) {
          throw new Error('session.json is not a session object');
        }
      } catch (err) {
        if (broken) broken.push({ dir, error: String(err.message).replace(/\s+/g, ' ').trim() });
        continue;
      }
      let touched = session.updatedAt || session.createdAt || null;
      try {
        const mtime = fs.statSync(file).mtime.toISOString();
        if (!touched || mtime > touched) touched = mtime;
      } catch {
        /* keep the recorded timestamp */
      }
      found.push({ dir, root, slug: session.slug || entry.name, session, touched: touched || '' });
    }
  }
  found.sort((a, b) => (a.touched < b.touched ? 1 : a.touched > b.touched ? -1 : 0));
  return found;
}

/**
 * Resolve which session a command acts on.
 * With --session, that slug. Without it, the most recently touched open session in this
 * project; then any open session; then the most recent session of any status here.
 */
export function resolveSession(slug, { project = findProjectRoot(), broken = null } = {}) {
  const all = listSessions({ project, broken });
  if (slug) {
    const hit = all.find((s) => s.slug === slug);
    if (!hit) {
      throw userError(
        `no session "${slug}" under ${storeRoots(project).join(' or ')}.`,
        [
          ...(broken || []).map((b) => `unreadable session at ${b.dir}: ${b.error}`),
          all.length ? `known sessions: ${all.map((s) => s.slug).join(', ')}` : 'no sessions exist yet.',
        ],
      );
    }
    return hit;
  }
  // A session belongs to this project when it says so, or when it physically lives in this
  // project's own store (which is where `--project` overrides put it).
  const projectStore = path.join(project, '.ponder');
  const here = (s) => s.session.project === project || s.root === projectStore;
  const open = all.filter((s) => s.session.status === 'open');
  return (
    open.find(here) ||
    open[0] ||
    all.find(here) ||
    all[0] ||
    null
  );
}

/** Like resolveSession but throws the actionable error when nothing is found. */
export function requireSession(slug, opts = {}) {
  const broken = opts.broken || [];
  const hit = resolveSession(slug, { ...opts, broken });
  if (!hit) {
    throw userError('no ponder session found in this project.', [
      ...broken.map((b) => `unreadable session at ${b.dir}: ${b.error}`),
      broken.length ? 'repair that session.json, or start a fresh pondering:' : 'start one:',
      '  ponder start "<subject>" --lens <lens>',
    ]);
  }
  return hit;
}

// ---------------------------------------------------------------------------
// locking
// ---------------------------------------------------------------------------

/** Sleep without spinning the CPU and without a dependency. */
function sleepSync(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

/**
 * Take an exclusive lock on a session directory.
 *
 * Every mutating command is a read-decide-write cycle over findings.json, units.json and
 * session.json. Two of them running at once clobber each other: the loser's findings never
 * land, and both hand out the same `f-NNNN`, which breaks "ids are never reused" (SPEC 3.3)
 * and leaves ledger.jsonl disagreeing with findings.json. `open(…, 'wx')` is atomic, so it
 * is the whole mechanism.
 *
 * Returns a release function. A store that cannot hold a lock at all degrades to no lock —
 * a safety net must not become a new way to fail.
 */
export function lockSession(dir, { timeoutMs = 10000, staleMs = 120000 } = {}) {
  const file = path.join(dir, '.lock');
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    let fd;
    try {
      fd = fs.openSync(file, 'wx');
    } catch (err) {
      if (err.code !== 'EEXIST') return () => {};
      let age = Infinity;
      try {
        age = Date.now() - fs.statSync(file).mtimeMs;
      } catch {
        age = Infinity; // it vanished between the open and the stat — try again
      }
      if (age > staleMs) {
        try {
          fs.unlinkSync(file);
        } catch {
          /* someone else cleared it first */
        }
        continue;
      }
      if (Date.now() >= deadline) {
        throw userError(`another ponder command is already working on ${path.basename(dir)}.`, [
          `lock: ${file}`,
          'wait for it to finish, or delete that file if the process that made it is gone.',
        ]);
      }
      sleepSync(60);
      continue;
    }
    try {
      fs.writeSync(fd, `${process.pid} ${new Date().toISOString()}\n`);
    } catch {
      /* the lock is the file's existence, not its contents */
    } finally {
      fs.closeSync(fd);
    }
    let released = false;
    const release = () => {
      if (released) return;
      released = true;
      try {
        fs.unlinkSync(file);
      } catch {
        /* already gone */
      }
    };
    // A crash between here and the release must not leave the session locked for ever;
    // 'exit' covers process.exit(), and staleMs covers a kill -9.
    process.once('exit', release);
    return release;
  }
}

// ---------------------------------------------------------------------------
// load / save
// ---------------------------------------------------------------------------

export function loadSession(dir) {
  const p = sessionPaths(dir);
  const session = readJSON(p.session, { label: 'session.json' });
  if (!session || typeof session !== 'object') throw userError(`${p.session} is not a session file.`);
  session.dir = dir;
  return session;
}

export function saveSession(dir, session, { touch = true } = {}) {
  const copy = { ...session };
  delete copy.dir;
  if (touch) copy.updatedAt = new Date().toISOString();
  writeJSON(sessionPaths(dir).session, copy);
  session.updatedAt = copy.updatedAt;
  return session;
}

export function loadUnits(dir) {
  const doc = readJSON(sessionPaths(dir).units, { label: 'units.json', optional: true });
  if (!doc) return { version: STATE_VERSION, lens: null, units: [] };
  if (!Array.isArray(doc.units)) doc.units = [];
  return doc;
}

export function saveUnits(dir, doc) {
  writeJSON(sessionPaths(dir).units, doc);
}

export function loadFindings(dir) {
  const doc = readJSON(sessionPaths(dir).findings, { label: 'findings.json', optional: true });
  if (!doc) return { version: STATE_VERSION, findings: [] };
  if (!Array.isArray(doc.findings)) doc.findings = [];
  return doc;
}

export function saveFindings(dir, doc) {
  writeJSON(sessionPaths(dir).findings, doc);
}

export function loadLedger(dir, { skipped = null } = {}) {
  return readJSONL(sessionPaths(dir).ledger, { label: 'ledger.jsonl', tolerant: true, skipped });
}

/**
 * Append to the permanent ledger and to this pass's deltas.jsonl.
 *
 * The ledger goes first, and the order is load-bearing (SPEC 3.6). A crash between the two
 * appends has to leave the **ledger** as the copy that is ahead, because the ledger is the
 * authority: everything else in the session is derivable from it, so a ledger-ahead session
 * can be rebuilt deterministically by `ponder verify --repair`. Were the pass file written
 * first, a crash would leave records living only in a per-pass file that the ledger — the
 * thing every other command replays — knows nothing about.
 */
export function recordDeltas(dir, pass, records) {
  if (!records || records.length === 0) return;
  // Create the pass directory before the ledger write, so the crash window is the append
  // itself and not a missing mkdir. `passDir` is idempotent.
  const file = passFile(dir, pass, 'deltas.jsonl', { create: true });
  appendJSONL(sessionPaths(dir).ledger, records);
  appendJSONL(file, records);
}

export function loadPassArtifact(dir, pass, name) {
  return readJSON(path.join(dir, 'passes', String(pass).padStart(2, '0'), name), { optional: true });
}

export function savePassArtifact(dir, pass, name, value) {
  writeJSON(passFile(dir, pass, name, { create: true }), value);
}

export function loadPassDeltas(dir, pass, { skipped = null } = {}) {
  return readJSONL(path.join(dir, 'passes', String(pass).padStart(2, '0'), 'deltas.jsonl'), {
    tolerant: true,
    skipped,
  });
}

/**
 * Every pass directory's `deltas.jsonl`, in pass order.
 *
 * This is the second, independent copy of the ledger that SPEC 3.4 guarantees:
 * `recordDeltas` writes the same records to `passes/NN/deltas.jsonl` and to `ledger.jsonl`
 * in one call, so the ledger is the ordered union of these files. Reconciliation (3.6)
 * compares the two, which is what makes appending a line to `ledger.jsonl` alone
 * insufficient to forge a session.
 *
 * Returns `[{ pass, records, present }]` for every `passes/NN` directory on disk, whether
 * or not it holds a deltas.jsonl — a pass directory that lost its deltas file is itself
 * something the caller needs to see.
 */
export function loadAllPassDeltas(dir, { skipped = null } = {}) {
  const root = path.join(dir, 'passes');
  let entries;
  try {
    entries = fs.readdirSync(root, { withFileTypes: true });
  } catch {
    return [];
  }
  const out = [];
  for (const entry of entries) {
    if (!entry.isDirectory() || !/^\d+$/.test(entry.name)) continue;
    const pass = Number(entry.name);
    const file = path.join(root, entry.name, 'deltas.jsonl');
    out.push({ pass, present: fs.existsSync(file), records: readJSONL(file, { tolerant: true, skipped }) });
  }
  out.sort((a, b) => a.pass - b.pass);
  return out;
}

/** Which artifacts a pass has produced. Derived from disk — no duplicated bookkeeping. */
export function passProgress(dir, pass) {
  return {
    pass,
    predict: loadPassArtifact(dir, pass, 'predict.json'),
    deliberation: loadPassArtifact(dir, pass, 'deliberation.json'),
    metrics: loadPassArtifact(dir, pass, 'metrics.json'),
    verdict: loadPassArtifact(dir, pass, 'verdict.json'),
  };
}

// ---------------------------------------------------------------------------
// creation
// ---------------------------------------------------------------------------

export function createSession({
  subject,
  lens,
  project,
  projectFrom = null,
  slug,
  maxPasses = 6,
  minPasses = 2,
  rubric = null,
  unitLabel = 'unit',
  dimensions = [],
}) {
  const root = ensureStoreRoot(project);
  const explicit = Boolean(slug);
  let finalSlug = explicit ? validateSlug(slug) : generateSlug(subject, lens, root);
  let dir = path.join(root, finalSlug);
  // mkdir without `recursive` is the atomic claim: EEXIST means somebody else owns this
  // slug. An existsSync check would leave a window in which two concurrent `ponder start`
  // runs both "win" and the second silently writes over the first.
  for (let attempt = 0; ; attempt++) {
    try {
      fs.mkdirSync(dir);
      break;
    } catch (err) {
      if (err.code !== 'EEXIST') {
        throw userError(`cannot create session directory ${dir}: ${err.code || err.message}`);
      }
      if (explicit || attempt >= 25) {
        throw userError(`session "${finalSlug}" already exists at ${dir}.`, [
          'pick another with --slug, or resume it:  ponder status --session ' + finalSlug,
        ]);
      }
      finalSlug = generateSlug(subject, lens, root);
      dir = path.join(root, finalSlug);
    }
  }
  fs.mkdirSync(path.join(dir, 'passes'), { recursive: true });
  const now = new Date().toISOString();
  const session = {
    version: STATE_VERSION,
    slug: finalSlug,
    subject,
    lens,
    rubric,
    unitLabel,
    dimensions,
    project,
    // How the root above was decided (SPEC 3.1). A session that cannot say this cannot say
    // how much a missing file is worth, and neither can whoever inherits it.
    projectFrom: projectFrom || { how: 'cwd', marker: null, cwd: project },
    maxPasses,
    minPasses,
    createdAt: now,
    updatedAt: now,
    status: 'open',
    currentPass: 1,
    phase: 'predict',
    oca: { enabled: false, reachable: false, sessionRef: null },
    history: [],
  };
  saveSession(dir, session, { touch: false });
  saveUnits(dir, { version: STATE_VERSION, lens, units: [] });
  saveFindings(dir, { version: STATE_VERSION, findings: [] });
  fs.writeFileSync(sessionPaths(dir).ledger, '', 'utf8');
  session.dir = dir;
  return { dir, root, session };
}

// ---------------------------------------------------------------------------
// the phase machine (SPEC 5.1)
// ---------------------------------------------------------------------------

/**
 * The phase a pass owes after `satisfied` is done.
 *
 * Pass 1:  predict → survey → appraise → deliberate → revise → judge → decide
 * Pass N>1: predict → deliberate → revise → judge → decide
 *
 * survey is skipped after pass 1 (amendments ride in as unit-add / unit-delete deltas),
 * and appraise folds into revise (`ponder delta` appraises by revising).
 */
export function phaseAfter(session, satisfied) {
  const firstPass = session.currentPass <= 1;
  switch (satisfied) {
    case 'predict':
      return firstPass ? 'survey' : 'deliberate';
    case 'survey':
      return 'appraise';
    case 'appraise':
      return 'deliberate';
    case 'deliberate':
      return 'revise';
    case 'revise':
      return 'judge';
    case 'judge':
      return 'decide';
    case 'decide':
      return 'predict';
    default:
      throw userError(`unknown phase "${satisfied}".`);
  }
}

/** Advance the session to the phase owed after `satisfied`. */
export function advancePhase(session, satisfied) {
  session.phase = phaseAfter(session, satisfied);
  return session.phase;
}

/** Exit 2 when a command arrives out of order, naming what the session actually owes. */
export function requirePhase(session, expected, command, hint) {
  if (session.phase === expected) return;
  const detail = [
    `session ${session.slug} is on pass ${session.currentPass} and owes ${session.phase}.`,
  ];
  if (hint) detail.push(hint);
  throw stateError(
    `out of order: "ponder ${command}" satisfies ${expected}, but this session owes ${session.phase}.`,
    detail,
  );
}

/** Exit 2 when a mutating command is aimed at a session that is no longer open. */
export function requireOpen(session, command) {
  if (session.status === 'open') return;
  throw stateError(
    `session ${session.slug} is ${session.status}; "ponder ${command}" only runs on an open session.`,
    [`read it with:  ponder report --session ${session.slug}`],
  );
}

export function isFirstPass(session) {
  return session.currentPass <= 1;
}
