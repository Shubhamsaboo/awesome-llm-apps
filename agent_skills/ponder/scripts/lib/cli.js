#!/usr/bin/env node
// ponder — a convergent deliberation loop for coding agents.
//
// Command dispatch, argument parsing, output formatting and exit codes.
//   0  success
//   1  user error        bad arguments, unreadable input, failed validation
//   2  state-machine violation   out-of-order phase, stop while coverage < 1.0
//
// Every command's last line of human output is `NEXT: <phase> — <command>`. That line is
// the mechanism that lets an agent resume this loop after its context is compacted, so it
// is printed on failure as well as on success.

import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

import * as fmt from './fmt.js';
import {
  PonderError,
  userError,
  stateError,
  findProjectRoot,
  resolveProjectRoot,
  projectOriginOf,
  projectRootIsGuessed,
  describeProjectOrigin,
  storeRoots,
  listSessions,
  requireSession,
  createSession,
  loadSession,
  saveSession,
  loadUnits,
  saveUnits,
  loadFindings,
  saveFindings,
  loadLedger,
  recordDeltas,
  loadPassArtifact,
  savePassArtifact,
  loadPassDeltas,
  loadAllPassDeltas,
  appendJSONL,
  passFile,
  sessionPaths,
  requirePhase,
  requireOpen,
  advancePhase,
  lockSession,
  writeText,
  readText,
} from './session.js';
import { loadLens, lensSummary, scaleSummary, availableLenses, lensDir, REPO_ROOT } from './lens.js';
import {
  parseDeltaSource,
  applyDeltas,
  seedEntries,
  normaliseUnits,
  describeDeltas,
  summariseDeltas,
  unitPathHistory,
  PERSPECTIVES,
  SEVERITIES,
} from './deltas.js';
import { reconcile, reconcileAt, requireReconciled, deriveState, classifyDivergences, planUnionRepair } from './reconcile.js';
import { computeMetrics, coverageOf, countFindings, priorMetricsFor, metacognitionTriggers } from './metrics.js';
import { computeVerdict, checkDecision, statusAfterStop, DECISIONS } from './verdict.js';
import { buildReport, buildApplyPlan, severityFloorFrom } from './report.js';

const DEFAULT_DSN = 'postgres://localhost/oneiro';

// ---------------------------------------------------------------------------
// the OCA bridge — loaded lazily and defensively
// ---------------------------------------------------------------------------
//
// The bridge contract says it never throws and always returns null on failure. The engine
// does not take that on trust: the import itself is dynamic (a missing or syntactically
// broken oca/bridge.js must not stop the engine) and every call is wrapped. SPEC 8.4.

const BRIDGE_URL = new URL('../oca/bridge.js', import.meta.url);
let bridgePromise = null;

async function bridge() {
  if (!bridgePromise) bridgePromise = import(BRIDGE_URL.href).then((m) => m, () => null);
  return bridgePromise;
}

async function oca(fn, ...args) {
  try {
    const mod = await bridge();
    if (!mod || typeof mod[fn] !== 'function') return null;
    return await mod[fn](...args);
  } catch {
    return null;
  }
}

function ocaMode() {
  const raw = (process.env.PONDER_OCA || 'auto').trim().toLowerCase();
  if (!['auto', 'on', 'off'].includes(raw)) {
    throw userError(`PONDER_OCA="${process.env.PONDER_OCA}" is not valid — use auto, on or off.`);
  }
  return raw;
}

function ocaDsn() {
  return process.env.PONDER_OCA_DSN || DEFAULT_DSN;
}

let probeCache;
async function ocaProbe() {
  if (probeCache === undefined) probeCache = await oca('probe');
  return probeCache;
}

/** Under PONDER_OCA=on an unreachable OCA is a hard error (SPEC 6). */
async function ocaGate() {
  if (ocaMode() !== 'on') return null;
  const probe = await ocaProbe();
  if (!probe || probe.reachable === false) {
    throw userError(`PONDER_OCA=on but the OCA is not reachable at ${ocaDsn()}.`, [
      probe && probe.note ? probe.note : 'the bridge returned nothing.',
      'set PONDER_OCA=auto to degrade silently, or off to stop trying.',
    ]);
  }
  return probe;
}

async function ocaState() {
  const mode = ocaMode();
  if (mode === 'off') {
    return { mode, enabled: false, reachable: false, dsn: ocaDsn(), note: 'PONDER_OCA=off' };
  }
  let enabled = false;
  try {
    const mod = await bridge();
    enabled = Boolean(mod && typeof mod.isEnabled === 'function' && mod.isEnabled());
  } catch {
    enabled = false;
  }
  const probe = await ocaProbe();
  return {
    mode,
    enabled,
    reachable: Boolean(probe && probe.reachable),
    dsn: (probe && probe.dsn) || ocaDsn(),
    note: probe ? probe.note || null : 'bridge unavailable',
  };
}

function ocaLine(state) {
  if (!state) return 'unknown';
  if (state.mode === 'off') return 'off (PONDER_OCA=off)';
  if (state.reachable) return `reachable — ${state.dsn}`;
  return `unreachable — ${state.dsn}${state.note ? ` (${state.note})` : ''}${state.mode === 'auto' ? '; degrading silently' : ''}`;
}

// ---------------------------------------------------------------------------
// argument parsing
// ---------------------------------------------------------------------------

const GLOBAL_FLAGS = { session: 'string', json: 'boolean', help: 'boolean' };

const COMMANDS = {
  start: {
    flags: { lens: 'string', project: 'string', slug: 'string', maxPasses: 'number', minPasses: 'number', rubric: 'string' },
    usage: 'ponder start "<subject>" --lens <lens> [--rubric <file>] [--project <path>] [--slug <slug>] [--max-passes N] [--min-passes N]',
    blurb: 'open a session on a subject',
  },
  units: {
    flags: { file: 'string', stdin: 'boolean', scan: 'string', strictScope: 'boolean' },
    usage: 'ponder units --file <units.json> | --stdin | --scan <dir> [--strict-scope]',
    blurb: 'seed the inventory (pass 1)',
  },
  predict: { flags: { churn: 'number', claim: 'string' }, usage: 'ponder predict --churn <0-1> --claim "<one line>"', blurb: 'state what this pass will find' },
  grade: { flags: { file: 'string', stdin: 'boolean' }, usage: 'ponder grade --file <findings.json> | --stdin', blurb: 'seed the finding set (pass 1)' },
  deliberate: {
    flags: { file: 'string', stdin: 'boolean', skip: 'boolean', why: 'string' },
    usage: 'ponder deliberate --file <deliberation.json> | --stdin | --skip --why "<reason>"',
    blurb: 'record the four perspectives',
  },
  delta: { flags: { file: 'string', stdin: 'boolean' }, usage: 'ponder delta --file <deltas.jsonl> | --stdin', blurb: 'apply revisions to the finding set' },
  judge: { flags: {}, usage: 'ponder judge', blurb: 'compute convergence signals and advise' },
  decide: { flags: { why: 'string' }, usage: 'ponder decide <continue|stop|escalate> --why "<reason>"', blurb: 'commit the decision' },
  status: { flags: {}, usage: 'ponder status', blurb: 'where am I, what do I owe' },
  verify: {
    flags: { repair: 'boolean' },
    usage: 'ponder verify [--repair]',
    blurb: 'replay the ledger and check the state files against it',
  },
  report: { flags: { out: 'string' }, usage: 'ponder report [--out <path>]', blurb: 'write report.md' },
  apply: { flags: { dryRun: 'boolean', severity: 'string' }, usage: 'ponder apply [--dry-run] [--severity must,should]', blurb: 'emit the ordered work plan' },
  list: { flags: {}, usage: 'ponder list', blurb: 'every session on this machine' },
  abort: { flags: { why: 'string' }, usage: 'ponder abort --why "<reason>"', blurb: 'close a session unfinished' },
  doctor: { flags: {}, usage: 'ponder doctor', blurb: 'environment and OCA reachability' },
  help: { flags: {}, usage: 'ponder help [<command>]', blurb: 'this list' },
  version: { flags: {}, usage: 'ponder version', blurb: 'print the engine version' },
};

const plural = (n, word) => `${n} ${pluralWord(n, word)}`;
const pluralWord = (n, word) => `${word}${n === 1 ? '' : 's'}`;
const kebab = (s) => s.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`);
const camel = (s) => s.replace(/-([a-z0-9])/g, (_, c) => c.toUpperCase());

function parseArgs(argv, spec) {
  const flags = { ...spec.flags, ...GLOBAL_FLAGS };
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--') {
      out._.push(...argv.slice(i + 1));
      break;
    }
    if (arg.startsWith('--')) {
      let name = arg.slice(2);
      let value = null;
      let inline = false;
      const eq = name.indexOf('=');
      if (eq !== -1) {
        value = name.slice(eq + 1);
        name = name.slice(0, eq);
        inline = true;
      }
      const key = camel(name);
      const type = flags[key];
      if (!type) {
        const known = Object.keys(flags).map((k) => `--${kebab(k)}`).join(' ');
        throw userError(`unknown flag --${name}.`, [`${spec.usage}`, `flags: ${known}`]);
      }
      if (type === 'boolean') {
        out[key] = inline ? !['false', '0', 'no'].includes(String(value).toLowerCase()) : true;
        continue;
      }
      if (!inline) {
        value = argv[++i];
        if (value === undefined) throw userError(`--${name} needs a value.`, [spec.usage]);
      }
      if (type === 'number') {
        const num = Number(value);
        if (!Number.isFinite(num)) throw userError(`--${name} needs a number (got "${value}").`, [spec.usage]);
        out[key] = num;
        continue;
      }
      out[key] = value;
      continue;
    }
    if (arg.length > 1 && arg.startsWith('-') && !/^-\d/.test(arg)) {
      throw userError(`unknown flag ${arg} — ponder uses long flags only.`, [spec.usage]);
    }
    out._.push(arg);
  }
  return out;
}

// ---------------------------------------------------------------------------
// output
// ---------------------------------------------------------------------------

let context = { session: null, dir: null };
let commandName = null;
let releaseLock = null;

class Out {
  constructor(command, args) {
    this.command = command;
    this.json = Boolean(args && args.json);
    this.payload = {};
    this.warnings = [];
  }

  say(...lines) {
    if (this.json) return;
    for (const line of lines) process.stdout.write(`${line}\n`);
  }

  blank() {
    this.say('');
  }

  warn(text) {
    this.warnings.push(text);
    if (!this.json) process.stdout.write(`${fmt.warn(text)}\n`);
  }

  data(obj) {
    Object.assign(this.payload, obj);
    return this;
  }

  finish(next) {
    const step = next || nextFor(context.session, { dir: context.dir });
    if (this.json) {
      process.stdout.write(
        JSON.stringify(
          {
            ok: true,
            command: this.command,
            session: context.session ? context.session.slug : null,
            ...this.payload,
            warnings: this.warnings,
            next: step,
          },
          null,
          2,
        ) + '\n',
      );
      return;
    }
    this.blank();
    process.stdout.write(`${fmt.nextLine(step.phase, step.command)}\n`);
  }
}

/** The concrete command the agent should run next. Never a phase name alone. */
function nextFor(session, { dir = null } = {}) {
  if (!session) {
    return { phase: 'start', command: 'ponder start "<subject>" --lens <lens>' };
  }
  const s = `--session ${session.slug}`;
  const pass = session.currentPass;
  const unit = session.unitLabel || 'unit';
  switch (session.status) {
    case 'converged':
    case 'stopped':
      return { phase: 'apply', command: `ponder report ${s}   # then: ponder apply --dry-run ${s}` };
    case 'applied':
      return { phase: 'done', command: `ponder report ${s}   # apply-plan.md is written; work it top to bottom` };
    case 'aborted':
      return { phase: 'done', command: `ponder list   # this session is aborted; open a new one with ponder start "<subject>" --lens <lens>` };
    default:
      break;
  }
  switch (session.phase) {
    case 'predict':
      return { phase: 'predict', command: `ponder predict --churn <0-1> --claim "<what pass ${pass} will find>" ${s}` };
    case 'survey':
      return { phase: 'survey', command: `ponder units --file units.json ${s}   # every ${unit}, exhaustively — coverage is measured against this list` };
    case 'appraise':
      return { phase: 'appraise', command: `ponder grade --file findings.json ${s}   # at least one graded finding per ${unit}` };
    case 'deliberate':
      return { phase: 'deliberate', command: `ponder deliberate --file deliberation.json ${s}   # or: ponder deliberate --skip --why "<reason>"` };
    case 'revise':
      return {
        phase: 'revise',
        command: `ponder delta --file deltas.jsonl ${s}${pass > 1 ? `   # pass ${pass} appraises by revising` : ''}`,
      };
    case 'judge':
      return { phase: 'judge', command: `ponder judge ${s}` };
    case 'decide': {
      let verdict = null;
      try {
        verdict = dir ? loadPassArtifact(dir, pass, 'verdict.json') : null;
      } catch {
        verdict = null;
      }
      // The hint has to agree with the gate, and the gate recomputes coverage live rather
      // than trusting verdict.json — a stale judge, or a hand-edited verdict claiming
      // "stop", must not make ponder advertise a command it is about to refuse.
      let live = null;
      try {
        live = dir ? coverageNow(dir) : null;
      } catch {
        live = null;
      }
      const gateShut = live ? live.coverage < 1 || live.ungraded.length > 0 : false;
      if (gateShut || (verdict && verdict.verdict === 'blocked')) {
        const ungraded = live ? live.ungraded : Array.isArray(verdict.ungraded) ? verdict.ungraded : [];
        const enumerated = live ? live.enumerated : ungraded.length;
        const why =
          enumerated === 0
            ? `blocked: the inventory is empty — stop is refused until it holds at least one graded ${unit}`
            : `blocked: ${plural(ungraded.length, `ungraded ${unit}`)} — stop is refused until coverage is 1.0`;
        return { phase: 'decide', command: `ponder decide continue --why "<reason>" ${s}   # ${why}` };
      }
      const advice = verdict ? verdict.verdict : null;
      return {
        phase: 'decide',
        command: `ponder decide ${advice || '<continue|stop|escalate>'} --why "<reason>" ${s}${advice ? `   # the engine advises ${advice}` : ''}`,
      };
    }
    default:
      return { phase: session.phase || 'status', command: `ponder status ${s}` };
  }
}

// ---------------------------------------------------------------------------
// shared helpers
// ---------------------------------------------------------------------------

/**
 * Resolve the session a command acts on.
 *
 * `lock: true` for every command that writes state. Ponder's mutating commands are all
 * read-decide-write over the same three files, so two of them in flight at once lose one
 * side's work and hand out the same finding id twice. The lock is released by main()'s
 * finally and, belt and braces, by the process 'exit' hook inside lockSession.
 */
function useSession(args, { open = false, command = '', lock = false } = {}) {
  const project = findProjectRoot();
  const hit = requireSession(args.session, { project });
  if (lock) releaseLock = lockSession(hit.dir);
  const session = loadSession(hit.dir);
  context = { session, dir: hit.dir };
  if (open) requireOpen(session, command);
  return { session, dir: hit.dir, root: hit.root };
}

/**
 * The `project` row.
 *
 * Every command that resolves a project root says which one it resolved and what decided
 * it. Silence is what let an unrelated ancestor `.ponder` capture a marker-less directory
 * and turn every relative path in the session into a guess nobody was told about.
 */
function projectRow(origin) {
  const where = origin.cwd && origin.cwd !== origin.root ? `cwd is ${origin.cwd}; ` : '';
  const inferred = origin.recorded === false ? ', inferred — this session predates the record' : '';
  return ['project', `${origin.root}  (${where}${describeProjectOrigin(origin)}${inferred})`];
}

/** The warning a guessed root earns, or null when a marker settled it. */
function guessedRootWarning(origin, { subject = 'This session' } = {}) {
  if (!projectRootIsGuessed(origin.how)) return null;
  const adopted = origin.how === 'ponder';
  return (
    `${subject} resolved its project root to ${origin.root} — ${describeProjectOrigin(origin)}. ` +
    `Every path in this session, and every phantom claim checked against one, resolves from there. ` +
    (adopted
      ? 'An existing .ponder is where sessions are kept, not proof of what the project is. '
      : '') +
    'If that is the wrong root, say so:  --project <path>'
  );
}

function readPayload(args, { what }) {
  if (args.stdin) {
    try {
      return fs.readFileSync(0, 'utf8');
    } catch (err) {
      throw userError(`cannot read ${what} from stdin: ${err.code || err.message}`);
    }
  }
  if (args.file) {
    const file = path.resolve(args.file);
    if (!fs.existsSync(file)) throw userError(`no such file: ${file}`, [`writing ${what} first is part of the phase.`]);
    return readText(file);
  }
  throw userError(`${what} needs --file <path> or --stdin.`);
}

function requireWhy(args, { what, min = 1 }) {
  const why = typeof args.why === 'string' ? args.why.trim() : '';
  if (why === '') throw userError(`${what} needs --why "<reason>".`);
  if (why.length < min) throw userError(`${what} needs a --why of at least ${min} characters (got ${why.length}).`);
  return why;
}

/**
 * Refuse to draw a conclusion from a session whose state files disagree with its ledger.
 *
 * Enforced by judge, decide, report and apply — the four commands that turn state into a
 * claim about the work. Not by predict, units, grade, delta, status or list: reconciliation
 * costs a full ledger replay, and the cost belongs where a conclusion is being drawn, not on
 * every keystroke of the loop. `ponder verify` runs it on demand.
 *
 * `state` lets a caller that has already read the three documents pass them in rather than
 * reading them twice. The per-pass delta files are always read here rather than accepted
 * from the caller: they are the second copy the union check (SPEC 3.4) compares the ledger
 * against, and a call site that forgot to supply them would silently skip that check.
 */
/** How many separate things a reconciliation found wrong, across all three kinds. */
function divergenceCount(result) {
  return result.divergences.length + result.ledgerProblems.length + (result.unionProblems || []).length;
}

/** The one line to lead with when there is only room for one. */
function firstDivergence(result) {
  if (result.divergences.length) return result.divergences[0].message;
  if (result.ledgerProblems.length) return `ledger.jsonl line ${result.ledgerProblems[0].line}: ${result.ledgerProblems[0].message}`;
  if (result.unionProblems && result.unionProblems.length) return result.unionProblems[0].message;
  return 'no detail was recorded.';
}

function reconciledOrRefuse(dir, session, command, state = null) {
  const result = state ? reconcile({ ...state, passDeltas: loadAllPassDeltas(dir) }) : reconcileAt(dir);
  return requireReconciled(result, { slug: session.slug, command });
}

function coverageNow(dir) {
  const units = loadUnits(dir).units;
  const findings = loadFindings(dir).findings;
  return { ...coverageOf(units, findings), units, findings };
}

function passesOf(dir, session) {
  const out = [];
  const last = Math.max(session.currentPass, session.history.length);
  for (let p = 1; p <= last; p++) {
    const predict = loadPassArtifact(dir, p, 'predict.json');
    const deliberation = loadPassArtifact(dir, p, 'deliberation.json');
    const metrics = loadPassArtifact(dir, p, 'metrics.json');
    const verdict = loadPassArtifact(dir, p, 'verdict.json');
    let deltas = [];
    try {
      deltas = loadPassDeltas(dir, p);
    } catch {
      deltas = [];
    }
    if (!predict && !deliberation && !metrics && !verdict && deltas.length === 0) continue;
    out.push({ pass: p, predict, deliberation, metrics, verdict, deltas });
  }
  return out;
}

function metricsRow(m) {
  if (!m) return 'not judged yet';
  return [
    `novelty ${fmt.num(m.novelty)}`,
    `churn ${fmt.num(m.churn)}`,
    `thrash ${fmt.num(m.thrash)}`,
    `surprise ${fmt.num(m.surprise)}`,
    `stall ${m.stall}`,
    `conf-floor ${fmt.num(m.confidenceFloor)}`,
    `voices ${m.voices}/4`,
  ].join('  ');
}

function normaliseDeliberation(raw, pass) {
  const doc = raw && typeof raw === 'object' && !Array.isArray(raw) ? raw : null;
  if (!doc && !Array.isArray(raw)) throw userError('deliberation must be a JSON object (or an array of perspective entries).');
  const perspectives = {};
  const push = (name, entry) => {
    const key = String(name || '').trim().toLowerCase();
    if (!PERSPECTIVES.includes(key)) {
      throw userError(`"${name}" is not a perspective — use ${PERSPECTIVES.join(', ')}.`);
    }
    const argument = typeof entry === 'string' ? entry : entry && entry.argument;
    if (typeof argument !== 'string' || argument.trim() === '') {
      throw userError(`the ${key} perspective has no "argument".`);
    }
    const confidence = entry && typeof entry.confidence === 'number' ? entry.confidence : null;
    if (confidence !== null && (confidence < 0 || confidence > 1)) {
      throw userError(`the ${key} perspective has a confidence outside 0-1.`);
    }
    perspectives[key] = { argument: argument.trim(), confidence };
  };

  const list = Array.isArray(raw) ? raw : Array.isArray(doc.perspectives) ? doc.perspectives : null;
  if (list) {
    for (const entry of list) push(entry && (entry.perspective || entry.name), entry);
  } else if (doc.perspectives && typeof doc.perspectives === 'object') {
    for (const [name, entry] of Object.entries(doc.perspectives)) push(name, entry);
  } else {
    // tolerate a flat {skeptic: "...", builder: {...}} document
    let found = 0;
    for (const name of PERSPECTIVES) {
      if (doc[name] !== undefined) {
        push(name, doc[name]);
        found++;
      }
    }
    if (found === 0) {
      throw userError('deliberation has no perspectives.', [
        'expected {"perspectives": {"skeptic": {"argument": "...", "confidence": 0.7}, ...}}',
      ]);
    }
  }
  if (Object.keys(perspectives).length === 0) throw userError('deliberation has no perspectives.');
  return {
    version: 1,
    pass,
    skipped: false,
    question: doc && typeof doc.question === 'string' ? doc.question : null,
    notes: doc && typeof doc.notes === 'string' ? doc.notes : null,
    perspectives,
    at: new Date().toISOString(),
  };
}

// ---------------------------------------------------------------------------
// commands
// ---------------------------------------------------------------------------

async function cmdStart(args) {
  const out = new Out('start', args);
  const subject = args._.join(' ').trim();
  if (!subject) throw userError('ponder start needs a subject.', [COMMANDS.start.usage]);
  if (!args.lens) throw userError('ponder start needs --lens <lens>.', [
    `installed: ${availableLenses().join(', ') || 'none'}`,
    'or supply your own:  --lens custom --rubric <file>',
  ]);
  const maxPasses = args.maxPasses === undefined ? 6 : args.maxPasses;
  const minPasses = args.minPasses === undefined ? 2 : args.minPasses;
  if (!Number.isInteger(maxPasses) || maxPasses < 1) throw userError('--max-passes must be an integer of at least 1.');
  if (!Number.isInteger(minPasses) || minPasses < 1) throw userError('--min-passes must be an integer of at least 1.');
  if (minPasses > maxPasses) throw userError(`--min-passes ${minPasses} is greater than --max-passes ${maxPasses}.`);

  const lens = loadLens(args.lens, { rubric: args.rubric });
  // Resolve the root, and keep how it was decided. Both are printed below and both are
  // written into session.json (SPEC 3.1): a root nothing established is a root every later
  // path check has to discount, and neither this agent nor the next one can discount what
  // it was never told.
  const origin = args.project
    ? { root: path.resolve(args.project), how: 'explicit', marker: null, cwd: path.resolve(process.cwd()) }
    : resolveProjectRoot();
  const project = origin.root;
  await ocaGate();

  const { dir, session } = createSession({
    subject,
    lens: lens.name,
    project,
    projectFrom: { how: origin.how, marker: origin.marker || null, cwd: origin.cwd },
    slug: args.slug,
    maxPasses,
    minPasses,
    rubric: args.rubric ? path.resolve(args.rubric) : null,
    unitLabel: lens.unit,
    dimensions: lens.dimensions,
  });
  context = { session, dir };

  const state = await ocaState();
  session.oca = { enabled: state.enabled, reachable: state.reachable, sessionRef: null };

  // Read the past before recording the present, or this session's own start row comes
  // back as "prior pondering".
  const priorRaw = await oca('priorPondering', subject);
  const prior = Array.isArray(priorRaw) ? priorRaw : [];

  const ref = await oca('recordStart', session);
  if (ref !== null && ref !== undefined) {
    session.oca.sessionRef = typeof ref === 'object' ? ref.id ?? ref.sessionRef ?? null : ref;
  }
  saveSession(dir, session);

  out.say(fmt.head('ponder start'));
  out.say(
    fmt.kv([
      ['session', `${session.slug}  ${fmt.statusLabel(session.status)}`],
      ['subject', subject],
      ['lens', `${lensSummary(lens)}`],
      // The dimension names, not just the count. Appraise grades against these, and an
      // agent that is never told them grades against whatever it happens to remember.
      // No pre-wrap: kv lays a long value out at the real terminal width and hangs the
      // continuations under the value column itself. Wrapping here at a guessed 74 and
      // hand-indenting to a guessed 12 only gave kv a value to re-flow.
      ['grade on', lens.dimensions.join(', ')],
      ['scale', scaleSummary(lens) || '—'],
      // Where this session thinks the software is, and why. Every relative path a unit or a
      // finding carries is resolved from here.
      projectRow(origin),
      ['store', dir],
      ['passes', `min ${minPasses}, max ${maxPasses}`],
      ['oca', ocaLine(state)],
    ]),
  );
  const guessed = guessedRootWarning(origin);
  if (guessed) out.warn(guessed);
  if (prior.length) {
    out.blank();
    out.say(fmt.head('Prior pondering'));
    for (const row of prior.slice(0, 5)) {
      const when = String(row.timestamp || row.at || '').slice(0, 10);
      const what = String(row.content || '').replace(/\s+/g, ' ').trim();
      const outcome = row.actual_outcome ? ` — ${String(row.actual_outcome).replace(/\s+/g, ' ').trim()}` : '';
      // These are one-line summaries and clipping them is right, but the budget has to
      // come from the terminal: a hard-coded 72 + 60 printed a 146-column line at every
      // width. 4 columns go to the bullet, 12 to the date and its gap.
      const budget = Math.max(24, fmt.termCols() - 16);
      const outcomeBudget = outcome ? Math.max(12, Math.floor(budget * 0.4)) : 0;
      out.say(fmt.bullet(`${when}  ${fmt.clip(what, budget - outcomeBudget)}${fmt.clip(outcome, outcomeBudget)}`));
    }
    out.blank();
    out.say(fmt.wrap('This subject has been pondered before. Start from what was already concluded, not from zero.', { indent: 2 }));
  }
  if (lens.enumerate) {
    out.blank();
    out.say(fmt.head(`How to enumerate ${lens.unit}s`));
    out.say(fmt.wrap(lens.enumerate, { indent: 2 }));
  }
  out.data({
    slug: session.slug,
    dir,
    subject,
    lens: lens.name,
    dimensions: lens.dimensions,
    unit: lens.unit,
    project,
    projectFrom: session.projectFrom,
    projectRootGuessed: projectRootIsGuessed(origin.how),
    prior,
    oca: state,
  });
  out.finish();
}

const IGNORED_SCAN_DIRS = new Set([
  '.git',
  '.hg',
  '.svn',
  '.ponder',
  'node_modules',
  'dist',
  'build',
  '.next',
  'out',
  'coverage',
  'vendor',
  '__pycache__',
  '.venv',
  'venv',
  'target',
]);

function discoverScopeFiles(projectRoot, scanTarget = '.') {
  const root = path.resolve(projectRoot || process.cwd());
  const absTarget = path.resolve(root, scanTarget);
  if (!fs.existsSync(absTarget)) {
    throw userError(`no such scan path: ${scanTarget} (resolved to ${absTarget})`);
  }
  const relTarget = path.relative(root, absTarget) || '.';
  if (relTarget.startsWith('..') || path.isAbsolute(relTarget)) {
    throw userError(`scan path "${scanTarget}" escapes project root ${root}.`);
  }

  // Prefer deterministic git index + untracked non-ignored files when inside a git worktree.
  try {
    const out = execFileSync(
      'git',
      ['-C', root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard', '--', relTarget],
      { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] },
    );
    const files = out
      .split('\0')
      .map((f) => f.trim())
      .filter((f) => f !== '' && !f.startsWith('.ponder/') && fs.existsSync(path.join(root, f)))
      .sort();
    if (files.length > 0) return files;
  } catch {
    // Fall back to deterministic filesystem walk when not a git repository.
  }

  const discovered = [];
  const walk = (currAbs) => {
    let stat;
    try {
      stat = fs.lstatSync(currAbs);
    } catch {
      return;
    }
    if (stat.isSymbolicLink()) return;
    if (stat.isFile()) {
      const rel = path.relative(root, currAbs).split(path.sep).join('/');
      if (rel && !rel.startsWith('.ponder/')) discovered.push(rel);
      return;
    }
    if (!stat.isDirectory()) return;
    const entries = fs.readdirSync(currAbs).sort();
    for (const entry of entries) {
      if (IGNORED_SCAN_DIRS.has(entry)) continue;
      walk(path.join(currAbs, entry));
    }
  };
  walk(absTarget);
  return discovered.sort();
}

function stripLineAnchor(p) {
  if (!p || typeof p !== 'string') return '';
  return p.replace(/:\d+(?:-\d+)?$/, '').replace(/^\.\//, '').replace(/\\/g, '/').trim();
}

async function cmdUnits(args) {
  const out = new Out('units', args);
  const { session, dir } = useSession(args, { open: true, command: 'units', lock: true });
  requirePhase(session, 'survey', 'units', 'pass 1 seeds the inventory; later passes amend it with unit-add / unit-delete deltas.');

  const projectRoot = session.project || findProjectRoot();
  const hasPayload = Boolean(args.file || args.stdin);
  if (!hasPayload && !args.scan) {
    throw userError('the unit inventory needs --file <path>, --stdin, or --scan <dir>.');
  }

  let raw;
  let scannedFiles = null;
  if (args.scan) {
    scannedFiles = discoverScopeFiles(projectRoot, args.scan);
    if (scannedFiles.length === 0) {
      throw userError(`--scan "${args.scan}" found 0 files under ${projectRoot}.`);
    }
  }

  if (hasPayload) {
    const text = readPayload(args, { what: 'the unit inventory' });
    let doc;
    try {
      doc = JSON.parse(text);
    } catch (err) {
      throw userError(`the unit inventory is not valid JSON: ${err.message}`);
    }
    raw = Array.isArray(doc) ? doc : doc && Array.isArray(doc.units) ? doc.units : null;
    if (!raw) throw userError('the unit inventory must be an array, or an object with a "units" array.');
  } else {
    raw = scannedFiles.map((relPath, idx) => ({
      id: `u${idx + 1}`,
      label: relPath,
      path: relPath,
      kind: session.unitLabel,
    }));
  }

  const units = normaliseUnits(raw, { pass: session.currentPass, lensUnit: session.unitLabel });

  // Audit enumerated unit paths against the filesystem scope when --scan or --strict-scope is given.
  let unenumeratedFiles = [];
  if (hasPayload && (args.scan || args.strictScope)) {
    const coveredPaths = new Set(units.map((u) => stripLineAnchor(u.path)).filter(Boolean));
    let expectedFiles = scannedFiles;
    if (!expectedFiles) {
      const dirs = Array.from(
        new Set(
          Array.from(coveredPaths)
            .map((p) => path.posix.dirname(p))
            .filter((d) => d && d !== '.'),
        ),
      );
      const gathered = new Set();
      for (const d of dirs.length ? dirs : ['.']) {
        try {
          for (const f of discoverScopeFiles(projectRoot, d)) gathered.add(f);
        } catch {
          // Ignore non-existent unit parent directories (Phantom Rule handles absent paths later).
        }
      }
      expectedFiles = Array.from(gathered).sort();
    }
    unenumeratedFiles = expectedFiles.filter((f) => !coveredPaths.has(f));
    if (args.strictScope && unenumeratedFiles.length > 0) {
      throw stateError(
        `survey omitted ${plural(unenumeratedFiles.length, 'file')} present on disk in scope.`,
        [
          ...unenumeratedFiles.slice(0, 10).map((f) => `missing from inventory: ${f}`),
          unenumeratedFiles.length > 10 ? `...and ${unenumeratedFiles.length - 10} more.` : null,
          'include every file in scope in units.json, or seed directly from disk with: ponder units --scan <dir>',
        ].filter(Boolean),
      );
    }
  }

  // Nothing enters a session's state without a ledger line (SPEC 3.4). The inventory is the
  // one thing that used to arrive silently: findings are seeded as `add` deltas, every later
  // amendment is a `unit-add` / `unit-edit` / `unit-delete` delta, but pass 1's units were
  // only ever written to units.json. That made units.json unverifiable, and an unverifiable
  // inventory is the coverage denominator taken on trust. `unit-seed` closes it.
  //
  // The ledger is written BEFORE units.json, and that order is the crash contract (SPEC 3.6):
  // the ledger is the authority, so a crash between the two must leave the ledger ahead —
  // a state `ponder verify --repair` can rebuild — never the state file, whose extra data
  // would exist nowhere else.
  recordDeltas(dir, session.currentPass, [
    {
      pass: session.currentPass,
      op: 'unit-seed',
      source: args.scan && !hasPayload ? 'scan' : 'units',
      perspective: null,
      why: `Pass ${session.currentPass} enumerated ${plural(units.length, session.unitLabel)} as the coverage denominator.`,
      ids: units.map((u) => u.id),
      units,
      at: new Date().toISOString(),
    },
  ]);
  saveUnits(dir, { version: 1, lens: session.lens, units });
  advancePhase(session, 'survey');
  saveSession(dir, session);

  const withPath = units.filter((u) => u.path).length;
  out.say(fmt.head(`ponder units — ${plural(units.length, session.unitLabel)} enumerated`));
  out.say(
    fmt.table(
      ['id', 'label', 'path'],
      units.slice(0, 40).map((u) => [u.id, fmt.clip(u.label, 44), u.path || fmt.c.grey('—')]),
    ),
  );
  if (units.length > 40) out.say(fmt.bullet(`… and ${units.length - 40} more (see units.json)`));
  out.blank();
  out.say(fmt.kv([['evidence', `${withPath} of ${units.length} carry a path`], ['coverage', `0 of ${units.length} graded — every one of these must be graded before this session can stop`]]));
  if (withPath < units.length) {
    out.warn(`${plural(units.length - withPath, session.unitLabel)} have no path. Path is the evidence anchor; findings without one are hard to defend.`);
  }
  if (unenumeratedFiles.length > 0) {
    out.warn(
      `disk scope scan found ${plural(unenumeratedFiles.length, 'unenumerated file')} not in units.json: ${unenumeratedFiles.slice(0, 5).join(', ')}${unenumeratedFiles.length > 5 ? ` (+${unenumeratedFiles.length - 5} more)` : ''}. Pass --strict-scope to block survey when files on disk are omitted.`,
    );
  }
  // The next phase is appraise, which grades against the lens rubric. Name the rubric here
  // rather than leaving the agent to remember it — this is the handoff into grading.
  const dims = Array.isArray(session.dimensions) ? session.dimensions : [];
  if (dims.length) {
    out.blank();
    out.say(fmt.head(`Grade every ${session.unitLabel} against these ${dims.length} dimensions`));
    out.say(fmt.wrap(dims.join(', '), { indent: 2 }));
  }
  out.data({ units: units.length, withPath, ids: units.map((u) => u.id), dimensions: dims, unenumeratedFiles });
  out.finish();
}

async function cmdPredict(args) {
  const out = new Out('predict', args);
  const { session, dir } = useSession(args, { open: true, command: 'predict', lock: true });
  requirePhase(session, 'predict', 'predict');

  if (args.churn === undefined) throw userError('ponder predict needs --churn <0-1>.', [COMMANDS.predict.usage]);
  if (!(args.churn >= 0 && args.churn <= 1)) throw userError(`--churn must be between 0 and 1 (got ${args.churn}).`);
  const claim = typeof args.claim === 'string' ? args.claim.trim() : '';
  if (claim === '') throw userError('ponder predict needs --claim "<one line>" — an unstated expectation cannot be scored.');

  const predict = { version: 1, pass: session.currentPass, churn: args.churn, claim, at: new Date().toISOString() };
  savePassArtifact(dir, session.currentPass, 'predict.json', predict);
  advancePhase(session, 'predict');
  saveSession(dir, session);

  const prior = loadPassArtifact(dir, session.currentPass - 1, 'metrics.json');
  out.say(fmt.head(`ponder predict — pass ${predict.pass}`));
  out.say(
    fmt.kv([
      ['churn', fmt.num(predict.churn)],
      ['claim', claim],
      ['last pass', prior ? `churn was ${fmt.num(prior.churn)}, surprise ${fmt.num(prior.surprise)}` : '—'],
    ]),
  );
  out.data({ predict });
  out.finish();
}

async function cmdGrade(args) {
  const out = new Out('grade', args);
  const { session, dir } = useSession(args, { open: true, command: 'grade', lock: true });
  requirePhase(session, 'appraise', 'grade', 'pass 1 seeds findings; later passes appraise by revising — ponder delta --file deltas.jsonl.');

  const text = readPayload(args, { what: 'the finding set' });
  let doc;
  try {
    doc = JSON.parse(text);
  } catch (err) {
    throw userError(`the finding set is not valid JSON: ${err.message}`);
  }
  const raw = Array.isArray(doc) ? doc : doc && Array.isArray(doc.findings) ? doc.findings : null;
  if (!raw) throw userError('the finding set must be an array, or an object with a "findings" array.');

  const unitsDoc = loadUnits(dir);
  const findingsDoc = loadFindings(dir);
  const result = applyDeltas(seedEntries(raw), {
    findings: findingsDoc.findings,
    units: unitsDoc.units,
    pass: session.currentPass,
    source: 'grade',
  });

  // Ledger first, state second (SPEC 3.6): a crash between the two leaves the ledger ahead,
  // which `ponder verify --repair` can rebuild from. The other order loses findings.
  recordDeltas(dir, session.currentPass, result.records);
  saveFindings(dir, { ...findingsDoc, findings: result.findings });
  advancePhase(session, 'appraise');
  saveSession(dir, session);

  const cov = coverageOf(unitsDoc.units, result.findings);
  const counts = countFindings(result.findings);
  out.say(fmt.head(`ponder grade — ${plural(result.records.length, 'finding')} seeded`));
  const bySeverity = {};
  for (const f of result.findings) bySeverity[f.severity] = (bySeverity[f.severity] || 0) + 1;
  out.say(
    fmt.kv([
      ['findings', `${counts.total} — ${SEVERITIES.map((s) => `${bySeverity[s] || 0} ${s}`).join(', ')}`],
      ['coverage', `${fmt.num(cov.coverage)} — ${cov.graded} of ${cov.enumerated} ${pluralWord(cov.enumerated, session.unitLabel)} graded`],
    ]),
  );
  if (cov.ungraded.length) {
    out.blank();
    out.say(fmt.c.red(`  ${plural(cov.ungraded.length, `ungraded ${session.unitLabel}`)} — this session cannot stop until every one carries a grade:`));
    out.say(fmt.idList(cov.ungraded));
  }
  out.data({ seeded: result.records.length, coverage: cov.coverage, ungraded: cov.ungraded, findings: counts });
  out.finish();
}

async function cmdDeliberate(args) {
  const out = new Out('deliberate', args);
  const { session, dir } = useSession(args, { open: true, command: 'deliberate', lock: true });
  requirePhase(session, 'deliberate', 'deliberate');
  // Both paths below write an OCA row (a `deliberations` row, or a `deliberation_skipped`
  // observation). Under PONDER_OCA=on that row may not be silently dropped — SPEC 6.
  await ocaGate();
  const pass = session.currentPass;

  if (args.skip) {
    const why = requireWhy(args, { what: 'skipping deliberation' });
    const doc = { version: 1, pass, skipped: true, why, perspectives: {}, at: new Date().toISOString() };
    savePassArtifact(dir, pass, 'deliberation.json', doc);
    advancePhase(session, 'deliberate');
    saveSession(dir, session);
    // The bridge returns the written row, or null when it wrote nothing — under
    // PONDER_OCA=off it is a no-op by design, and under auto an unreachable OCA degrades
    // silently. Say which of those happened. This is the one place the engine tells an
    // agent its reasoning was logged, so it must not claim a row it did not write.
    const observation = await oca(
      'recordObservation',
      session,
      'deliberation_skipped',
      `Pass ${pass} skipped deliberation: ${why}`,
      { pass, why },
      'medium',
      'Run the four perspectives next pass, or accept that this pass revised without argument.',
    );
    const recorded = Boolean(observation);
    out.say(fmt.head(`ponder deliberate — pass ${pass} skipped`));
    out.say(
      fmt.kv([
        ['why', why],
        [
          'recorded',
          recorded
            ? 'deliberation.json, and a metacognitive observation: deliberation_skipped'
            : `deliberation.json only — no observation was written (${ocaMode() === 'off' ? 'PONDER_OCA=off' : 'the OCA was not reachable'})`,
        ],
      ]),
    );
    out.warn('a pass that never argued with itself is a weak pass. Expect low voices and a warning if you stop here.');
    out.data({ skipped: true, why, observationRecorded: recorded });
    out.finish();
    return;
  }

  const text = readPayload(args, { what: 'the deliberation' });
  let raw;
  try {
    raw = JSON.parse(text);
  } catch (err) {
    throw userError(`the deliberation is not valid JSON: ${err.message}`);
  }
  const doc = normaliseDeliberation(raw, pass);
  savePassArtifact(dir, pass, 'deliberation.json', doc);
  advancePhase(session, 'deliberate');

  // SPEC 6.1 puts the `deliberations` row at `deliberate`. Its `resolution` is the pass's
  // delta summary, which does not exist yet, so the row goes in now with the four arguments
  // and `judge` closes it. Remember the id on the session so judge can find the open row;
  // a null (OCA off or unreachable) simply means judge inserts the row complete instead.
  const opened = await oca('recordDeliberation', session, pass, doc);
  if (opened && opened.deliberationId) {
    if (!session.oca || typeof session.oca !== 'object') session.oca = {};
    if (!session.oca.deliberations || typeof session.oca.deliberations !== 'object') session.oca.deliberations = {};
    session.oca.deliberations[String(pass)] = opened.deliberationId;
  }
  saveSession(dir, session);

  const heard = Object.keys(doc.perspectives);
  const silent = PERSPECTIVES.filter((p) => !heard.includes(p));
  out.say(fmt.head(`ponder deliberate — pass ${pass}, ${heard.length} of 4 perspectives`));
  // Not a kv block, so the value column has to be worked out here: the widest
  // "  name     (0.70) " prefix across the voices that actually spoke. Every argument then
  // wraps to the terminal and hangs under that one column, first line included — the old
  // hard-coded `cols: 76` with a 12-space hang under an 18-column prefix ran the first line
  // of every argument six columns past the edge at any width.
  const spoke = PERSPECTIVES.filter((name) => doc.perspectives[name]);
  const confOf = (entry) => (entry.confidence === null ? '' : ` (${fmt.num(entry.confidence)})`);
  const valueCol = spoke.reduce((m, name) => Math.max(m, 2 + 8 + fmt.width(confOf(doc.perspectives[name])) + 1), 0);
  const argCols = Math.max(24, fmt.termCols() - valueCol);
  for (const name of spoke) {
    const entry = doc.perspectives[name];
    const conf = confOf(entry);
    const lead = `  ${fmt.c.bold(name.padEnd(8))}${fmt.c.grey(conf)}`;
    const gap = ' '.repeat(Math.max(1, valueCol - 2 - 8 - fmt.width(conf)));
    const body = fmt.wrap(entry.argument, { cols: argCols, indent: 0, prose: true }).split('\n');
    out.say(`${lead}${gap}${body[0]}`);
    for (const line of body.slice(1)) out.say(' '.repeat(valueCol) + line);
  }
  if (silent.length) out.warn(`silent: ${silent.join(', ')}. Each perspective owns one delta op — a silent voice is a revision that will not happen.`);
  out.blank();
  out.say(
    fmt.wrap(
      `Now emit the deltas those arguments imply: skeptic → delete, builder → edit, dreamer → add, empath → change. Every delta needs a why.`,
      { indent: 2 },
    ),
  );
  out.data({ perspectives: doc.perspectives, heard, silent });
  out.finish();
}

async function cmdDelta(args) {
  const out = new Out('delta', args);
  const { session, dir } = useSession(args, { open: true, command: 'delta', lock: true });
  requirePhase(session, 'revise', 'delta');
  const pass = session.currentPass;

  const text = readPayload(args, { what: 'the delta batch' });
  const entries = parseDeltaSource(text, { label: args.file ? path.resolve(args.file) : 'stdin' });
  const unitsDoc = loadUnits(dir);
  const findingsDoc = loadFindings(dir);
  const before = countFindings(findingsDoc.findings);
  const deltaOrigin = projectOriginOf(session);

  const result = applyDeltas(entries, {
    findings: findingsDoc.findings,
    units: unitsDoc.units,
    pass,
    source: 'delta',
    // A phantom claim names a path that is supposed to not exist. It is resolved from the
    // subject's own root, so the check is against the software being pondered.
    projectRoot: session.project,
    // ...and how much a missing file is worth depends on how that root was decided. A root
    // no project marker established makes "the file is not there" a statement about the
    // directory we are looking in, so the claim is refused rather than recorded (SPEC 3.5).
    projectRootGuessed: projectRootIsGuessed(deltaOrigin.how),
    projectRootOrigin: describeProjectOrigin(deltaOrigin),
    // ...and it is checked against every path the unit has ever carried, read off the
    // ledger, not just the one units.json holds now. `unit-edit` can move a path, and a
    // claim checked only against the current value is a two-delta hole in the coverage
    // gate: edit the path to a filename that does not exist, then certify the absence.
    unitPaths: unitPathHistory(loadLedger(dir)),
  });

  // Ledger first, state second (SPEC 3.6). The ledger is the authority, so the only crash
  // window this leaves is a ledger that is ahead of its own view — deterministically
  // rebuildable by `ponder verify --repair`. The reverse order leaves unrecoverable state.
  recordDeltas(dir, pass, result.records);
  saveFindings(dir, { ...findingsDoc, findings: result.findings });
  saveUnits(dir, { ...unitsDoc, units: result.units });
  advancePhase(session, 'revise');
  saveSession(dir, session);

  const cov = coverageOf(result.units, result.findings);
  const after = countFindings(result.findings);
  const added = result.records.filter((r) => r.op === 'add').map((r) => r.id);

  // `voices` is who spoke in this pass's deliberation (SPEC 4). Delta attribution is shown
  // beside it, but a perspective that argued "nothing to change here" has still spoken, so
  // it is the deliberation — not the delta count — that decides whether the pass argued.
  const deliberation = loadPassArtifact(dir, pass, 'deliberation.json');
  const spoke =
    deliberation && !deliberation.skipped && deliberation.perspectives
      ? Object.keys(deliberation.perspectives).filter((p) => PERSPECTIVES.includes(p))
      : [];
  const phantoms = result.records.filter((r) => r.op === 'unit-delete' && r.removal === 'phantom');
  const droppedUngraded = result.records.filter((r) => r.op === 'unit-delete' && r.removal === 'removed-ungraded');

  out.say(fmt.head(`ponder delta — pass ${pass}, ${plural(result.records.length, 'delta')} applied`));
  out.say(
    fmt.kv([
      ['ops', describeDeltas(result.summary)],
      ['voices', `${spoke.length} of 4 spoke — ${spoke.join(', ') || 'none'}`],
      ['delta voices', `${result.summary.voices.length} of 4 emitted — ${result.summary.voices.join(', ') || 'none'}`],
      ['new ids', added.length ? added.join(', ') : '—'],
      ['findings', `${after.total} total · ${after.open} open · ${after.retracted} retracted (was ${before.total}/${before.open}/${before.retracted})`],
      ['coverage', `${fmt.num(cov.coverage)} — ${cov.graded} of ${cov.enumerated} ${pluralWord(cov.enumerated, session.unitLabel)} graded`],
    ]),
  );
  if (spoke.length < 3) {
    out.warn(
      deliberation && deliberation.skipped
        ? 'this pass skipped deliberation. A pass that never argued with itself is a weak place to stop.'
        : `${spoke.length === 0 ? 'no perspectives' : plural(spoke.length, 'perspective')} spoke in this pass's deliberation. A pass that heard fewer than three is a weak place to stop.`,
    );
  }
  if (phantoms.length) {
    out.blank();
    out.say(fmt.c.yellow(`  ${plural(phantoms.length, `phantom ${session.unitLabel}`)} dropped from the coverage denominator:`));
    for (const r of phantoms) {
      out.say(
        fmt.bullet(
          r.verification === 'verified-missing'
            ? `${r.target} — verified: ${r.verifiedPath} does not exist`
            : Array.isArray(r.pathsChecked)
              ? // The path was edited. Every version of it was checked and none exists, but
                // the engine will not certify an absence about a target that moved (SPEC 3.5).
                `${r.target} — UNVERIFIED: its path was edited, so all ${plural(r.pathsChecked.length, 'version')} of it were checked (${r.pathsChecked.join(', ')}) and none exists — but a moved target is one the engine cannot certify an absence about`
              : `${r.target} — UNVERIFIED: no path to check the claim against`,
          { indent: 4 },
        ),
      );
    }
    out.say(fmt.wrap('Every one of these is permanent and appears under Phantom units in report.md.', { indent: 2 }));
  }
  if (droppedUngraded.length) {
    out.blank();
    out.say(
      fmt.c.red(
        `  ${plural(droppedUngraded.length, `${session.unitLabel}`)} removed without ever being graded — still counted against coverage:`,
      ),
    );
    out.say(fmt.idList(droppedUngraded.map((r) => r.target)));
    out.say(
      fmt.wrap(
        'A delete cannot manufacture coverage. Grade them, or delete them again with "phantom": true if they do not exist in the software and let the engine check.',
        { indent: 2 },
      ),
    );
  }
  if (cov.ungraded.length) {
    out.blank();
    out.say(fmt.c.red(`  ${plural(cov.ungraded.length, `ungraded ${session.unitLabel}`)}:`));
    out.say(fmt.idList(cov.ungraded));
  }
  out.data({
    applied: result.records.length,
    ops: result.summary.byOp,
    voices: spoke,
    deltaVoices: result.summary.voices,
    added,
    coverage: cov.coverage,
    ungraded: cov.ungraded,
    removedUngraded: cov.removedUngraded,
    phantoms: phantoms.map((r) => ({ id: r.target, verification: r.verification })),
    findings: after,
  });
  out.finish();
}

async function cmdJudge(args) {
  const out = new Out('judge', args);
  const { session, dir } = useSession(args, { open: true, command: 'judge', lock: true });
  requirePhase(session, 'judge', 'judge');
  await ocaGate();
  const pass = session.currentPass;

  const units = loadUnits(dir).units;
  const findings = loadFindings(dir).findings;
  const damaged = [];
  const ledger = loadLedger(dir, { skipped: damaged });
  // Every signal below is computed from units.json and findings.json. If those files do not
  // say what the ledger says they must, the signals are measuring a fiction — so this is
  // checked before a single one of them is computed (SPEC 3.6).
  reconciledOrRefuse(dir, session, 'judge', { ledger, units, findings, skippedLedgerLines: damaged });
  const predict = loadPassArtifact(dir, pass, 'predict.json');
  const priorMetrics = priorMetricsFor(loadPassArtifact, dir, pass);
  // SPEC 4: `voices` counts who spoke in the deliberation, so the metrics need the
  // deliberation, not only the ledger.
  const deliberationDoc = loadPassArtifact(dir, pass, 'deliberation.json');

  const metrics = computeMetrics({ session, units, findings, ledger, pass, predict, priorMetrics, deliberation: deliberationDoc });
  const observations = await oca('openObservations', session);
  const advice = computeVerdict({ metrics, session, priorMetrics, observations });

  savePassArtifact(dir, pass, 'metrics.json', metrics);
  const verdict = {
    version: 1,
    pass,
    verdict: advice.verdict,
    reason: advice.reason,
    rule: advice.rule,
    message: advice.message,
    notes: advice.notes,
    ungraded: advice.ungraded,
    signals: {
      coverage: metrics.coverage,
      novelty: metrics.novelty,
      churn: metrics.churn,
      thrash: metrics.thrash,
      surprise: metrics.surprise,
      stall: metrics.stall,
      confidenceFloor: metrics.confidenceFloor,
      voices: metrics.voices,
      deltaVoices: metrics.deltaVoices,
    },
    removedUngraded: metrics.removedUngraded,
    phantoms: metrics.phantoms,
    advisedAt: new Date().toISOString(),
    decision: null,
    why: null,
    override: false,
    warnings: [],
    decidedAt: null,
  };
  savePassArtifact(dir, pass, 'verdict.json', verdict);
  advancePhase(session, 'judge');
  saveSession(dir, session);

  await oca('recordPass', session, pass, metrics, predict);
  const deliberation = loadPassArtifact(dir, pass, 'deliberation.json');
  if (deliberation && !deliberation.skipped) {
    let resolution = 'deltas unreadable';
    try {
      resolution = describeDeltas(summariseDeltas(loadPassDeltas(dir, pass)));
    } catch {
      /* the OCA summary must never be the thing that fails a judge */
    }
    // Phase two: close the row `deliberate` opened. If there is no open row to close —
    // the OCA was unreachable at deliberate, or this session predates the two-phase write —
    // insert it complete now, so the pass is never left without a deliberations row.
    const openId = session.oca && session.oca.deliberations ? session.oca.deliberations[String(pass)] : null;
    const resolved = openId ? await oca('resolveDeliberation', session, openId, resolution) : null;
    if (!resolved || !resolved.resolved) {
      await oca('recordDeliberation', session, pass, deliberation, resolution);
    }
  }
  const triggers = metacognitionTriggers(metrics);
  for (const t of triggers) {
    await oca('recordObservation', session, t.type, t.description, t.evidence, t.severity, t.intervention);
  }

  const firstPass = Number(pass) <= 1;
  out.say(fmt.head(`ponder judge — pass ${pass} of ${session.maxPasses}`));
  out.say(
    fmt.table(
      ['signal', 'value', 'reads as'],
      [
        ['coverage', fmt.signal(metrics.coverage, { good: 1, bad: 0.999, invert: true }), `${metrics.units.graded} of ${metrics.units.enumerated} ${pluralWord(metrics.units.enumerated, session.unitLabel)} graded`],
        ['novelty', fmt.num(metrics.novelty), firstPass ? 'pass 1 has no previous pass to be new against' : `revising adds ÷ live findings${metrics.deltas.seeded ? ` (${metrics.deltas.seeded} seeded by grade, excluded)` : ''}`],
        ['churn', fmt.num(metrics.churn), firstPass ? 'pass 1 revised nothing — it created the baseline' : 'revising deltas ÷ live findings'],
        ['thrash', fmt.signal(metrics.thrash, { good: 0.1, bad: 0.25 }), firstPass ? 'nothing to reverse yet' : `${metrics.reversals.length} reversing delta${metrics.reversals.length === 1 ? '' : 's'}`],
        ['surprise', fmt.num(metrics.surprise), firstPass ? 'scored from pass 2, once churn exists' : predict ? `predicted ${fmt.num(metrics.predictedChurn)}, got ${fmt.num(metrics.churn)}` : 'no prediction on file'],
        ['stall', String(metrics.stall), 'consecutive passes under 0.02 churn'],
        ['confidenceFloor', fmt.signal(metrics.confidenceFloor, { good: 0.1, bad: 0.2 }), 'open must-findings still guessing'],
        ['voices', `${metrics.voices}/4`, metrics.deliberationSkipped ? 'deliberation was skipped' : metrics.voiceNames.join(', ') || 'nobody argued'],
        ['delta voices', `${metrics.deltaVoices}/4`, metrics.deltaVoiceNames.join(', ') || 'no perspective emitted a delta'],
      ],
    ),
  );
  if (metrics.reversals.length) {
    out.blank();
    out.say(fmt.head('  Reversals'));
    for (const r of metrics.reversals.slice(0, 6)) out.say(fmt.bullet(`${r.kind}: ${r.note}`, { indent: 4 }));
  }
  out.blank();
  out.say(`  advice: ${fmt.verdictLabel(advice.verdict)} — ${advice.message}`);
  for (const note of advice.notes) out.say(fmt.bullet(note, { indent: 4 }));
  if (firstPass) {
    out.blank();
    out.say(
      fmt.wrap(
        '— is not a zero. Novelty, churn, thrash and surprise measure change against a previous pass, and pass 1 has none. They start reading on pass 2.',
        { indent: 2 },
      ),
    );
  }
  if (advice.verdict === 'blocked' && advice.ungraded.length) {
    const dropped = new Set(metrics.removedUngraded || []);
    out.blank();
    out.say(fmt.c.red(`  ${plural(advice.ungraded.length, `ungraded ${session.unitLabel}`)} — "ponder decide stop" will be refused:`));
    out.say(fmt.idList(advice.ungraded.map((id) => (dropped.has(id) ? `${id}  (deleted ungraded — still counts)` : id))));
  }
  if (metrics.phantoms.length) {
    out.blank();
    out.say(fmt.c.yellow(`  ${plural(metrics.phantoms.length, `phantom ${session.unitLabel}`)} out of the denominator:`));
    for (const ph of metrics.phantoms) {
      out.say(fmt.bullet(`${ph.id} — ${ph.verification} (pass ${ph.pass})`, { indent: 4 }));
    }
  }
  for (const t of triggers) out.warn(`${t.type}: ${t.description}`);
  if (damaged.length) {
    out.warn(
      `${plural(damaged.length, 'unreadable line')} in ledger.jsonl (${damaged.map((d) => d.line).join(', ')}) ${damaged.length === 1 ? 'was' : 'were'} skipped — every signal above is computed from the rest. Repair the file if you want ${damaged.length === 1 ? 'it' : 'them'} counted.`,
    );
  }
  out.data({
    metrics,
    verdict: advice.verdict,
    reason: advice.reason,
    message: advice.message,
    // The notes carry the part of the advice that says what to do about it — including why
    // a deleted-ungraded unit still counts. A --json-only agent needs that as much as a
    // human reader does.
    notes: advice.notes,
    ungraded: advice.ungraded,
    removedUngraded: metrics.removedUngraded,
    phantoms: metrics.phantoms,
    observations: triggers,
    ledgerSkipped: damaged,
  });
  out.finish();
}

async function cmdDecide(args) {
  const out = new Out('decide', args);
  const { session, dir } = useSession(args, { open: true, command: 'decide', lock: true });
  requirePhase(session, 'decide', 'decide');
  // The coverage gate is recomputed here from units.json and findings.json, so those two
  // files decide whether a stop is honest. They only get that authority if they agree with
  // the ledger (SPEC 3.6) — a forged unit entry is a forged gate.
  reconciledOrRefuse(dir, session, 'decide');
  const pass = session.currentPass;

  const decision = String(args._[0] || '').trim().toLowerCase();
  if (!decision) throw userError(`ponder decide needs a decision: ${DECISIONS.join(', ')}.`, [COMMANDS.decide.usage]);
  // Only `decide stop` writes an OCA row (`ponder_converged`), so only it is coupled.
  if (decision === 'stop') await ocaGate();

  const verdict = loadPassArtifact(dir, pass, 'verdict.json');
  const metrics = loadPassArtifact(dir, pass, 'metrics.json');
  if (!verdict || !metrics) {
    throw stateError(`pass ${pass} has not been judged.`, [`run:  ponder judge --session ${session.slug}`]);
  }

  // Recomputed live: the gate must not be beatable with a stale metrics.json.
  const cov = coverageNow(dir);
  const check = checkDecision({
    session,
    decision,
    why: args.why,
    advice: verdict.verdict,
    adviceReason: verdict.reason,
    metrics,
    coverage: cov.coverage,
    ungraded: cov.ungraded,
    enumerated: cov.enumerated,
    removedUngraded: cov.removedUngraded,
  });

  verdict.decision = decision;
  verdict.why = check.reason;
  verdict.override = check.override;
  verdict.warnings = check.warnings;
  verdict.decidedAt = new Date().toISOString();
  verdict.coverageAtDecision = cov.coverage;
  savePassArtifact(dir, pass, 'verdict.json', verdict);

  session.history.push({
    pass,
    verdict: verdict.verdict,
    decision,
    reason: check.reason,
    override: check.override,
    at: verdict.decidedAt,
  });

  let closing = null;
  if (decision === 'stop') {
    session.status = statusAfterStop(verdict.verdict, verdict.reason);
    closing = session.status;
  } else {
    session.currentPass = pass + 1;
    advancePhase(session, 'decide');
  }
  saveSession(dir, session);

  if (decision === 'stop') {
    const counts = countFindings(cov.findings);
    await oca(
      'recordConverged',
      session,
      `${session.subject} (${session.lens}): ${pass} passes, ${counts.total} findings, ${counts.open} open, ${counts.retracted} retracted, coverage ${cov.coverage.toFixed(2)}, ended ${session.status} (${verdict.reason}).`,
    );
  }

  out.say(fmt.head(`ponder decide — pass ${pass}: ${decision}`));
  out.say(
    fmt.kv([
      ['advice', `${verdict.verdict} (${verdict.reason})`],
      ['decision', check.override ? `${decision}  ${fmt.c.yellow('OVERRIDE')}` : decision],
      ['why', check.reason],
      ['session', closing ? `${fmt.statusLabel(closing)} after ${pass} pass${pass === 1 ? '' : 'es'}` : `open — pass ${session.currentPass} of ${session.maxPasses} next`],
    ]),
  );
  for (const w of check.warnings) out.warn(w);
  if (check.override) {
    out.blank();
    out.say(fmt.wrap(`This override is permanent. report.md will carry it under Overrides with the reason above.`, { indent: 2 }));
  }
  if (decision === 'escalate') {
    out.blank();
    out.say(
      fmt.wrap(
        'Escalation means the next pass must be different, not longer: rotate which perspective leads, widen the evidence you look at, or split the subject into two sessions.',
        { indent: 2 },
      ),
    );
  }
  out.data({ decision, advice: verdict.verdict, reason: verdict.reason, why: check.reason, override: check.override, status: session.status, currentPass: session.currentPass });
  out.finish();
}

async function cmdStatus(args) {
  const out = new Out('status', args);
  const { session, dir } = useSession(args, { command: 'status' });
  const units = loadUnits(dir).units;
  const findings = loadFindings(dir).findings;
  const cov = coverageOf(units, findings);
  const counts = countFindings(findings);
  const pass = session.currentPass;
  const thisPassMetrics = loadPassArtifact(dir, pass, 'metrics.json');
  const metrics = thisPassMetrics || loadPassArtifact(dir, pass - 1, 'metrics.json');
  const verdict = loadPassArtifact(dir, pass, 'verdict.json') || loadPassArtifact(dir, pass - 1, 'verdict.json');
  const last = session.history.length ? session.history[session.history.length - 1] : null;
  const state = await ocaState();
  const predict = loadPassArtifact(dir, pass, 'predict.json');
  const statusOrigin = projectOriginOf(session);

  const owed =
    session.status === 'open'
      ? `${session.phase}${pass > 1 && session.phase === 'revise' ? ' (appraise + revise in one command)' : ''}`
      : `nothing — session is ${session.status}`;

  out.say(fmt.head(`ponder status — ${session.slug}`));
  const rows = [
    ['session', `${session.slug}  ${fmt.statusLabel(session.status)}`],
    ['subject', session.subject],
    ['lens', `${session.lens} — unit = ${session.unitLabel}, ${(session.dimensions || []).length} dimensions`],
    // status is what an agent runs after losing its context. The rubric it grades against
    // has to be recoverable from here, not only from the pack it read at start.
    ['grade on', (session.dimensions || []).join(', ') || '—'],
    ['pass', `${pass} of ${session.maxPasses}  (min ${session.minPasses})`],
    ['owes', owed],
    ['coverage', `${fmt.num(cov.coverage)} — ${cov.graded} of ${cov.enumerated} ${pluralWord(cov.enumerated, session.unitLabel)} graded`],
    ['findings', `${counts.total} total · ${counts.open} open · ${counts.resolved} resolved · ${counts.deferred || 0} deferred · ${counts.retracted} retracted`],
    ['prediction', predict ? `churn ${fmt.num(predict.churn)} — "${fmt.clip(predict.claim, 60)}"` : '— (this pass has not predicted yet)'],
    [metrics ? `signals p${metrics.pass}` : 'signals', metricsRow(metrics)],
    [
      'last verdict',
      last
        ? `pass ${last.pass}: ${last.verdict} → decided ${last.decision}${last.override ? ' (OVERRIDE)' : ''} — "${fmt.clip(last.reason, 56)}"`
        : verdict
          ? `pass ${verdict.pass}: ${verdict.verdict} (${verdict.reason}) — undecided`
          : 'none yet',
    ],
    ['oca', ocaLine(state)],
    // status is what an agent runs after losing its context, so it has to say where this
    // session thinks the software is and what decided that — a wrong root turns every path
    // check in the session into a guess, silently.
    projectRow(statusOrigin),
    ['store', dir],
  ];
  out.say(fmt.kv(rows));
  const statusGuessed = guessedRootWarning(statusOrigin, { subject: `Session ${session.slug}` });
  if (statusGuessed) out.warn(statusGuessed);
  if (cov.ungraded.length) {
    const dropped = new Set(cov.removedUngraded);
    out.blank();
    out.say(fmt.c.red(`  ${plural(cov.ungraded.length, `ungraded ${session.unitLabel}`)} — stop is refused until this list is empty:`));
    out.say(fmt.idList(cov.ungraded.map((id) => (dropped.has(id) ? `${id}  (deleted ungraded — still counts)` : id))));
  }
  if (cov.phantoms.length) {
    out.blank();
    out.say(fmt.c.yellow(`  ${plural(cov.phantoms.length, `phantom ${session.unitLabel}`)} out of the denominator:`));
    for (const ph of cov.phantoms) out.say(fmt.bullet(`${ph.id} — ${ph.verification} (pass ${ph.pass})`, { indent: 4 }));
  }
  if (session.history.length > 1) {
    out.blank();
    out.say(fmt.head('  History'));
    out.say(
      fmt.table(
        ['pass', 'advice', 'decision', 'reason'],
        session.history.map((h) => [String(h.pass), h.verdict, h.decision + (h.override ? ' *' : ''), fmt.clip(h.reason, 52)]),
        { indent: 4 },
      ),
    );
  }
  out.data({
    slug: session.slug,
    dir,
    project: session.project,
    projectFrom: statusOrigin.recorded ? session.projectFrom : { ...statusOrigin, inferred: true },
    projectRootGuessed: projectRootIsGuessed(statusOrigin.how),
    status: session.status,
    subject: session.subject,
    lens: session.lens,
    unit: session.unitLabel,
    dimensions: session.dimensions || [],
    pass,
    maxPasses: session.maxPasses,
    minPasses: session.minPasses,
    phase: session.phase,
    coverage: cov.coverage,
    ungraded: cov.ungraded,
    removedUngraded: cov.removedUngraded,
    phantoms: cov.phantoms,
    findings: counts,
    metrics,
    verdict,
    history: session.history,
    oca: state,
  });
  out.finish();
}

/**
 * Rebuild a ledger-ahead session's state files from the ledger (SPEC 3.6).
 *
 * This is the other half of the write ordering. `recordDeltas` appends to `ledger.jsonl`
 * before anything writes `units.json`, `findings.json` or the per-pass `deltas.jsonl`, so
 * the only state a crash mid-command can leave is one where the ledger holds records the
 * rest of the session has not caught up to. Every one of those records determines what the
 * files must contain, so the repair is a replay and a write — no guessing, no reconstruction
 * from partial evidence.
 *
 * A **state-ahead** session is refused instead. A unit or a finding that no ledger record
 * ever created exists in exactly one place, so there is nothing to rebuild it from: it is
 * either a forgery or an unrecoverable loss, and both are a hard error. With the ordering
 * above it should also be unreachable.
 *
 * Returns `{ repaired, rebuilt, blocked }`.
 */
function repairFromLedger(dir, session, result) {
  const { repairable, unrecoverable } = classifyDivergences(result.divergences);
  const union = planUnionRepair(loadLedger(dir), loadAllPassDeltas(dir));
  const blocked = [];

  if (result.ledgerProblems.length) {
    blocked.push(
      `ledger.jsonl contradicts itself in ${plural(result.ledgerProblems.length, 'place')}. Repair rebuilds the session FROM the ledger, so a ledger that does not describe a reachable session is nothing to rebuild from.`,
    );
  }
  if (result.skippedLedgerLines.length) {
    blocked.push(
      `${plural(result.skippedLedgerLines.length, 'line')} of ledger.jsonl (${result.skippedLedgerLines.map((l) => l.line).join(', ')}) could not be parsed, so the replay is already missing records. Repair those lines by hand first.`,
    );
  }
  for (const d of unrecoverable) {
    blocked.push(
      `${d.message} That is state running AHEAD of the ledger: the data exists in no other copy, so nothing can rebuild it. This is a hard error by design (SPEC 3.6).`,
    );
  }
  for (const p of union.problems) blocked.push(p.message);

  if (blocked.length) return { repaired: false, rebuilt: [], blocked };
  if (!repairable.length && !union.appends.length) return { repaired: false, rebuilt: [], blocked: [] };

  const derived = deriveState(loadLedger(dir));
  const rebuilt = [];

  const unitIds = new Set(repairable.filter((d) => d.scope === 'unit').map((d) => d.id));
  const findingIds = new Set(repairable.filter((d) => d.scope === 'finding').map((d) => d.id));

  if (unitIds.size) {
    const doc = loadUnits(dir);
    saveUnits(dir, { version: doc.version || 1, lens: doc.lens || session.lens, units: derived.units });
    rebuilt.push(
      `units.json — ${plural(derived.units.length, 'unit')} rebuilt from the ledger (${[...unitIds].sort().join(', ')} ${unitIds.size === 1 ? 'was' : 'were'} behind it)`,
    );
  }
  if (findingIds.size) {
    const doc = loadFindings(dir);
    saveFindings(dir, { version: doc.version || 1, findings: derived.findings });
    rebuilt.push(
      `findings.json — ${plural(derived.findings.length, 'finding')} rebuilt from the ledger (${[...findingIds].sort().join(', ')} ${findingIds.size === 1 ? 'was' : 'were'} behind it)`,
    );
  }
  for (const a of union.appends) {
    appendJSONL(passFile(dir, a.pass, 'deltas.jsonl', { create: true }), a.records);
    rebuilt.push(
      `passes/${String(a.pass).padStart(2, '0')}/deltas.jsonl — ${plural(a.records.length, 'record')} appended to catch it up to the ledger`,
    );
  }
  return { repaired: rebuilt.length > 0, rebuilt, blocked: [] };
}

async function cmdVerify(args) {
  const out = new Out('verify', args);
  const { session, dir } = useSession(args, { command: 'verify', lock: Boolean(args.repair) });
  let result = reconcileAt(dir);
  let repair = null;

  if (args.repair && !result.ok) {
    repair = repairFromLedger(dir, session, result);
    if (repair.repaired) result = reconcileAt(dir);
  }

  const c = result.counts;

  out.say(fmt.head(`ponder verify — ${session.slug}${args.repair ? ' --repair' : ''}`));
  out.say(
    fmt.kv([
      ['ledger', `${plural(c.records, 'record')} — ${c.seeds} unit-seed, ${c.adds} add, ${c.unitAdds} unit-add, ${c.unitEdits} unit-edit, ${c.unitDeletes} unit-delete`],
      ['passes', `${c.passRecords} of those records also in the per-pass delta files, across ${c.passFiles} pass ${c.passFiles === 1 ? 'directory' : 'directories'}`],
      ['units', `${c.actualUnits} in units.json, ${c.expectedUnits} derived from the ledger`],
      ['findings', `${c.actualFindings} in findings.json, ${c.expectedFindings} derived from the ledger`],
      ['result', result.ok ? fmt.c.green('reconciles — every unit and every finding is accounted for by a ledger record') : fmt.c.red(`${plural(divergenceCount(result), 'divergence')}`)],
    ]),
  );
  if (result.skippedLedgerLines.length) {
    out.warn(
      `${plural(result.skippedLedgerLines.length, 'unreadable line')} in ledger.jsonl (${result.skippedLedgerLines.map((s) => s.line).join(', ')}) ${result.skippedLedgerLines.length === 1 ? 'was' : 'were'} left out of the replay. Repair ${result.skippedLedgerLines.length === 1 ? 'it' : 'them'}: an unreadable ledger line is state nothing can account for.`,
    );
  }
  if (repair && repair.repaired) {
    out.blank();
    out.say(fmt.head('Repaired from the ledger'));
    for (const line of repair.rebuilt) out.say(fmt.bullet(line));
    out.blank();
    out.say(
      fmt.wrap(
        'The ledger is the authority (SPEC 3.6) and it was ahead of its own view — the shape a crash between the ledger append and the state write leaves behind. Every rebuilt value came off a ledger record; nothing was inferred.',
        { indent: 2 },
      ),
    );
  } else if (repair && repair.blocked.length) {
    out.blank();
    out.say(fmt.c.red('  --repair cannot rebuild this session:'));
    for (const line of repair.blocked) out.say(fmt.wrap(line, { indent: 4 }));
  } else if (args.repair && result.ok && !repair) {
    out.blank();
    out.say(fmt.wrap('Nothing to repair — the state files already match the ledger.', { indent: 2 }));
  }

  out.data({
    ok: result.ok,
    divergences: result.divergences,
    ledgerProblems: result.ledgerProblems,
    unionProblems: result.unionProblems,
    ledgerSkipped: result.skippedLedgerLines,
    repaired: repair ? repair.repaired : false,
    rebuilt: repair ? repair.rebuilt : [],
    unrepairable: repair ? repair.blocked : [],
    counts: c,
  });

  // A divergence is the same refusal here as at a decision point: exit 2, the same
  // diagnosis, and in --json the same {ok:false, error, detail, next} an agent already
  // knows how to read. verify exists to be run early, not to be a gentler answer.
  requireReconciled(result, { slug: session.slug, command: 'verify' });
  out.finish();
}

async function cmdReport(args) {
  const out = new Out('report', args);
  const { session, dir } = useSession(args, { command: 'report' });
  const units = loadUnits(dir).units;
  const findings = loadFindings(dir).findings;
  const damaged = [];
  const ledger = loadLedger(dir, { skipped: damaged });
  // report.md is the artefact people read instead of the session. It must not narrate a
  // state the ledger never produced (SPEC 3.6).
  reconciledOrRefuse(dir, session, 'report', { ledger, units, findings, skippedLedgerLines: damaged });
  const passes = passesOf(dir, session);
  let lens = null;
  try {
    lens = loadLens(session.lens, { rubric: session.rubric });
  } catch {
    lens = null; // a report must not fail because a lens pack moved
  }
  const markdown = buildReport({ session, units, findings, ledger, passes, lens });
  const outPath = args.out ? path.resolve(args.out) : sessionPaths(dir).report;
  writeText(outPath, markdown);

  const cov = coverageOf(units, findings);
  const counts = countFindings(findings);
  const overrides = passes.filter((p) => p.verdict && p.verdict.override).length;
  out.say(fmt.head('ponder report'));
  out.say(
    fmt.kv([
      ['written', outPath],
      ['passes', String(passes.length)],
      ['coverage', `${fmt.num(cov.coverage)} — ${cov.graded} of ${cov.enumerated} ${pluralWord(cov.enumerated, session.unitLabel)}`],
      ['findings', `${counts.total} total · ${counts.open} open · ${counts.retracted} retracted`],
      ['overrides', overrides ? `${overrides} (surfaced permanently in the report)` : 'none'],
      ['bytes', String(Buffer.byteLength(markdown))],
    ]),
  );
  if (damaged.length) {
    out.warn(
      `${plural(damaged.length, 'unreadable line')} in ledger.jsonl (${damaged.map((d) => d.line).join(', ')}) ${damaged.length === 1 ? 'was' : 'were'} skipped — the Ledger section below counts only the lines that parsed.`,
    );
  }
  out.data({ path: outPath, bytes: Buffer.byteLength(markdown), passes: passes.length, coverage: cov.coverage, overrides, ledgerSkipped: damaged });
  out.finish();
}

async function cmdApply(args) {
  const out = new Out('apply', args);
  const { session, dir } = useSession(args, { command: 'apply', lock: true });
  const dryRun = Boolean(args.dryRun);
  const { floor, error } = severityFloorFrom(args.severity);
  if (error) throw userError(`"${error}" is not a severity — use ${SEVERITIES.join(', ')}.`);
  // A committed apply writes an episodic row; --dry-run writes nothing anywhere, so it
  // stays usable against a dead OCA the same way status and report do.
  if (!dryRun) await ocaGate();

  // An abandoned pondering must not be able to quietly become an applied one. This holds
  // for --dry-run too: there is no plan to preview out of a session that was walked away
  // from, only findings nobody stood behind.
  if (session.status === 'aborted') {
    throw stateError(`session ${session.slug} was aborted; there is no plan to apply.`, [
      `it was closed unfinished${session.abortedWhy ? `: ${session.abortedWhy}` : '.'}`,
      'apply turns a finished pondering into work. An abandoned one has to be reopened, not applied:',
      `  ponder start "${session.subject}" --lens ${session.lens}`,
      `  ponder report --session ${session.slug}    # read what it did find`,
    ]);
  }

  if (!dryRun && session.status === 'open') {
    throw stateError(`session ${session.slug} is still open on pass ${session.currentPass} (${session.phase}).`, [
      'apply is separate and explicit — it never runs as part of a pass.',
      `finish the pondering:  ponder decide stop --why "<reason>" --session ${session.slug}`,
      `or preview the plan:   ponder apply --dry-run --session ${session.slug}`,
    ]);
  }

  const units = loadUnits(dir).units;
  const findings = loadFindings(dir).findings;
  // apply is where findings become work someone actually does. A fabricated finding must
  // not reach that list, so the plan is only built from a state the ledger accounts for
  // (SPEC 3.6). --dry-run is checked too: the preview is the plan.
  reconciledOrRefuse(dir, session, 'apply');
  const plan = buildApplyPlan({ session, units, findings, severityFloor: floor });
  const outPath = sessionPaths(dir).applyPlan;

  if (!dryRun) {
    writeText(outPath, plan.markdown);
    session.status = 'applied';
    session.appliedAt = new Date().toISOString();
    session.appliedSeverity = floor;
    saveSession(dir, session);
    // The fixed bridge interface has no apply hook; use one only if the bridge grew it.
    await oca(
      'recordApply',
      session,
      `${session.subject} (${session.lens}): apply plan for ${plan.selected.length} findings at ${floor} or above across ${plural(plan.groups.length, session.unitLabel)}.`,
    );
  }

  out.say(fmt.head(`ponder apply${dryRun ? ' --dry-run' : ''} — ${plural(plan.selected.length, 'finding')} at ${floor} or above`));
  out.blank();
  out.say(plan.markdown.split('\n').slice(2).join('\n'));
  if (!dryRun) {
    out.say(fmt.kv([['written', outPath], ['session', `${fmt.statusLabel('applied')} — the pondering is closed`]]));
  } else {
    out.say(fmt.kv([['dry run', 'nothing written, session untouched']]));
  }
  out.data({ dryRun, severity: floor, findings: plan.selected.map((f) => f.id), groups: plan.groups.length, path: dryRun ? null : outPath, markdown: plan.markdown });
  out.finish(
    dryRun
      ? { phase: 'apply', command: `ponder apply --severity ${floor} --session ${session.slug}   # writes apply-plan.md and closes the session` }
      : { phase: 'done', command: `work apply-plan.md top to bottom: ${outPath}` },
  );
}

async function cmdList(args) {
  const out = new Out('list', args);
  const project = findProjectRoot();
  const broken = [];
  const sessions = listSessions({ project, broken });
  out.say(fmt.head(`ponder list — ${sessions.length} session${sessions.length === 1 ? '' : 's'}`));
  if (sessions.length === 0) {
    out.say(fmt.wrap('No sessions yet.', { indent: 2 }));
  } else {
    const rows = sessions.map(({ slug, session, dir }) => {
      let coverage = '—';
      try {
        const cov = coverageOf(loadUnits(dir).units, loadFindings(dir).findings);
        coverage = fmt.num(cov.coverage);
      } catch {
        coverage = '—';
      }
      return [
        slug,
        fmt.statusLabel(session.status),
        `${session.currentPass}/${session.maxPasses}`,
        session.status === 'open' ? session.phase : '—',
        coverage,
        session.lens,
        fmt.clip(session.subject, 40),
      ];
    });
    out.say(fmt.table(['slug', 'status', 'pass', 'owes', 'cov', 'lens', 'subject'], rows));
  }
  out.say('');
  out.say(fmt.kv([['stores', storeRoots(project).join('  ')]]));
  if (broken.length) {
    out.blank();
    out.say(fmt.c.red(`  ${broken.length} session ${broken.length === 1 ? 'directory' : 'directories'} could not be read — ${broken.length === 1 ? 'it is' : 'they are'} on disk but invisible to every command:`));
    for (const b of broken) out.say(fmt.bullet(`${b.dir} — ${b.error}`, { indent: 4 }));
  }
  const resume = sessions.find((s) => s.session.status === 'open');
  if (resume) context = { session: loadSession(resume.dir), dir: resume.dir };
  out.data({
    broken,
    sessions: sessions.map(({ slug, dir, session }) => ({
      slug,
      dir,
      status: session.status,
      subject: session.subject,
      lens: session.lens,
      pass: session.currentPass,
      phase: session.phase,
      updatedAt: session.updatedAt,
    })),
  });
  out.finish(resume ? undefined : { phase: 'start', command: 'ponder start "<subject>" --lens <lens>' });
}

async function cmdAbort(args) {
  const out = new Out('abort', args);
  const { session, dir } = useSession(args, { open: true, command: 'abort', lock: true });
  const why = requireWhy(args, { what: 'aborting a session' });
  session.status = 'aborted';
  session.abortedAt = new Date().toISOString();
  session.abortedWhy = why;
  session.history.push({ pass: session.currentPass, verdict: 'aborted', decision: 'abort', reason: why, override: false, at: session.abortedAt });
  saveSession(dir, session);
  out.say(fmt.head(`ponder abort — ${session.slug}`));
  out.say(fmt.kv([['status', fmt.statusLabel('aborted')], ['pass', `${session.currentPass}, owing ${session.phase}`], ['why', why]]));
  out.blank();
  out.say(fmt.wrap('Nothing was deleted. The findings, the ledger and every pass artifact stay on disk and can still be reported.', { indent: 2 }));
  out.data({ status: 'aborted', why });
  out.finish();
}

async function cmdDoctor(args) {
  const out = new Out('doctor', args);
  const origin = resolveProjectRoot();
  const project = origin.root;
  const problems = [];

  // The configuration that produced the bug this check exists for: a directory with no
  // project markers of its own, sitting under someone else's `.ponder`, which it then
  // adopts as its project root. Every relative path resolves from there, and a path that
  // does not resolve is worth nothing — which is exactly when a phantom claim wants to be
  // worth something.
  if (origin.how === 'ponder' && origin.root !== origin.cwd) {
    problems.push(
      `no project marker (${['.git', 'package.json', '…'].join(', ')}) anywhere above ${origin.cwd}, so the project root was adopted from the .ponder at ${origin.root}. That store may belong to something else entirely, and every relative path here resolves from it. Start sessions with:  ponder start "<subject>" --lens <lens> --project <path>`,
    );
  }

  const lenses = availableLenses();
  if (lenses.length === 0) problems.push(`no lens packs in ${lensDir()} — every session needs one.`);

  // Not BRIDGE_URL.pathname: a URL percent-encodes, so a checkout at "/opt/pon der" would
  // be probed as "/opt/pon%20der" and doctor would report a perfectly good bridge missing.
  const bridgeFile = path.join(REPO_ROOT, 'oca', 'bridge.js');
  const bridgeMod = await bridge();
  if (!fs.existsSync(bridgeFile)) problems.push(`no OCA bridge at ${bridgeFile} — the engine runs, but nothing is remembered.`);
  else if (!bridgeMod) problems.push(`oca/bridge.js exists but failed to load — the engine is degrading to no-OCA.`);

  let psql = null;
  try {
    psql = execFileSync('psql', ['--version'], { encoding: 'utf8', timeout: 5000 }).trim();
  } catch {
    psql = null;
  }

  const state = await ocaState();
  if (state.mode === 'on' && !state.reachable) problems.push(`PONDER_OCA=on but the OCA is unreachable at ${state.dsn}.`);

  const brokenSessions = [];
  const sessions = listSessions({ project, broken: brokenSessions });
  for (const b of brokenSessions) problems.push(`unreadable session at ${b.dir}: ${b.error}`);
  const open = sessions.filter((s) => s.session.status === 'open');

  // The same question asked of every session already on disk, not just of this directory.
  // doctor is what an agent runs on a checkout it inherited, and a session whose root was
  // adopted from a stray .ponder is one whose path evidence never meant what it looked like.
  const adopted = [];
  for (const s of sessions) {
    const o = projectOriginOf(s.session);
    if (o.how !== 'ponder') continue;
    adopted.push({ slug: s.slug, project: o.root });
    problems.push(
      `session ${s.slug} adopted ${o.root} as its project root from a .ponder rather than from a project marker. Its paths, its evidence anchors and every phantom claim it checked resolve from there. Confirm the root before trusting them:  ponder status --session ${s.slug}`,
    );
  }

  // Reconcile every session on the machine (SPEC 3.6). doctor is the command an agent runs
  // on a checkout it inherited, so it is the right place to be told that a session's state
  // files no longer match its ledger — before it spends a pass working on them.
  const unreconciled = [];
  for (const s of sessions) {
    let result;
    try {
      result = reconcileAt(s.dir);
    } catch (err) {
      problems.push(`cannot reconcile session ${s.slug}: ${err.message}`);
      continue;
    }
    if (result.ok) continue;
    const n = divergenceCount(result);
    unreconciled.push({
      slug: s.slug,
      dir: s.dir,
      divergences: result.divergences,
      ledgerProblems: result.ledgerProblems,
      unionProblems: result.unionProblems,
    });
    problems.push(
      `session ${s.slug} does not reconcile with its ledger — ${plural(n, 'divergence')}. ${firstDivergence(result)} Run:  ponder verify --session ${s.slug}`,
    );
  }
  const stores = storeRoots(project).map((root) => {
    let writable = false;
    try {
      fs.mkdirSync(root, { recursive: true });
      fs.accessSync(root, fs.constants.W_OK);
      writable = true;
    } catch {
      writable = false;
    }
    return { root, writable };
  });
  if (!stores.some((s) => s.writable)) problems.push('no writable session store — neither the project nor the home directory accepts .ponder/.');

  out.say(fmt.head('ponder doctor'));
  out.say(
    fmt.kv([
      ['node', `${process.version}${Number(process.versions.node.split('.')[0]) >= 20 ? '' : '  (ponder needs node 20+)'}`],
      ['engine', path.join(REPO_ROOT, 'lib', 'cli.js')],
      ['lenses', lenses.length ? `${lensDir()} — ${lenses.join(', ')}` : fmt.c.red(`${lensDir()} — none installed`)],
      ['bridge', fs.existsSync(bridgeFile) ? `${bridgeFile}${bridgeMod ? '' : fmt.c.red(' — failed to load')}` : fmt.c.red('missing')],
      ['psql', psql || fmt.c.yellow('not on PATH — the OCA bridge cannot talk to Postgres')],
      // What a session started here would call the project, and what decided it.
      projectRootIsGuessed(origin.how) ? [projectRow(origin)[0], fmt.c.yellow(projectRow(origin)[1])] : projectRow(origin),
      ['PONDER_OCA', `${state.mode}  (dsn ${state.dsn})`],
      ['oca', ocaLine(state)],
      ...stores.map((s, i) => [i === 0 ? 'store' : '', `${s.root} ${s.writable ? fmt.c.green('writable') : fmt.c.red('not writable')}`]),
      ['sessions', `${sessions.length} total, ${open.length} open`],
      [
        'ledger',
        sessions.length === 0
          ? 'no sessions to reconcile'
          : unreconciled.length === 0
            ? fmt.c.green(sessions.length === 1 ? 'the one session reconciles with its ledger' : `all ${sessions.length} sessions reconcile with their ledgers`)
            : fmt.c.red(`${plural(unreconciled.length, 'session')} ${unreconciled.length === 1 ? 'does' : 'do'} not reconcile — ${unreconciled.map((u) => u.slug).join(', ')}`),
      ],
    ]),
  );
  if (problems.length) {
    out.blank();
    out.say(fmt.head('  Problems'));
    for (const p of problems) out.say(fmt.bullet(fmt.c.red(p), { indent: 4 }));
  }
  out.data({
    node: process.version,
    lenses,
    bridge: fs.existsSync(bridgeFile),
    bridgeLoaded: Boolean(bridgeMod),
    psql,
    oca: state,
    project,
    projectFrom: { how: origin.how, marker: origin.marker || null, cwd: origin.cwd },
    projectRootGuessed: projectRootIsGuessed(origin.how),
    adoptedRoots: adopted,
    stores,
    sessions: sessions.length,
    open: open.length,
    broken: brokenSessions,
    unreconciled,
    problems,
  });

  const resume = open[0];
  if (resume) context = { session: loadSession(resume.dir), dir: resume.dir };
  out.finish(resume ? undefined : { phase: 'start', command: 'ponder start "<subject>" --lens <lens>' });

  if (problems.length) process.exitCode = 1;
}

function usageText() {
  const lines = [];
  lines.push(fmt.head('ponder — a convergent deliberation loop for coding agents'));
  lines.push('');
  lines.push(fmt.wrap('Run repeated passes over a subject. Each pass revises the last. The engine measures whether stopping is honest and refuses to let a pass be silently skipped.', { indent: 2 }));
  lines.push('');
  lines.push(fmt.head('  Commands'));
  for (const [name, spec] of Object.entries(COMMANDS)) {
    // Every command ponder answers to is in this list, `version` included. A command that
    // runs but is documented nowhere is a command nobody can find: SPEC 5 lists it, so does
    // this, and the conformance suite checks both.
    lines.push(`    ${fmt.c.bold(name.padEnd(11))}${spec.blurb}`);
    lines.push(`    ${' '.repeat(11)}${fmt.c.grey(spec.usage)}`);
  }
  lines.push('');
  lines.push(fmt.head('  Everywhere'));
  lines.push(`    ${fmt.c.grey('--session <slug>   act on a named session (default: the most recently touched open one)')}`);
  lines.push(`    ${fmt.c.grey('--json             machine-readable output on stdout')}`);
  // Both of these have always worked and both are documented in the skill's protocol
  // reference. A flag that works, is written down, and is missing from `ponder help` is
  // exactly the "command nobody can find" SPEC 5 is guarding against.
  lines.push(`    ${fmt.c.grey('--help             usage for one command (same as: ponder help <command>)')}`);
  lines.push(`    ${fmt.c.grey('--version          print the engine version (same as: ponder version)')}`);
  lines.push('');
  lines.push(fmt.head('  Environment'));
  lines.push(`    ${fmt.c.grey('PONDER_OCA         auto (default) | on | off')}`);
  lines.push(`    ${fmt.c.grey(`PONDER_OCA_DSN     default ${DEFAULT_DSN}`)}`);
  lines.push(`    ${fmt.c.grey('PONDER_LENS_DIR    override the lens pack directory')}`);
  lines.push(`    ${fmt.c.grey('NO_COLOR           disable colour (also off when stdout is not a TTY)')}`);
  lines.push(`    ${fmt.c.grey('COLUMNS            layout width, clamped to 40-120 (default: the TTY, or 88 off one)')}`);
  lines.push(`    ${fmt.c.grey('PONDER_NO_WRAP     =1 never wrap human output (--json never wraps either)')}`);
  lines.push('');
  lines.push(fmt.head('  Exit codes'));
  lines.push(`    ${fmt.c.grey('0 success · 1 user error · 2 state-machine violation (out of order, or stop while blocked)')}`);
  return lines.join('\n');
}

async function cmdHelp(args) {
  const out = new Out('help', args);
  const which = args._[0];
  if (which && COMMANDS[which]) {
    out.say(fmt.head(`ponder ${which} — ${COMMANDS[which].blurb}`));
    out.say('');
    out.say(`  ${COMMANDS[which].usage}`);
    out.data({ command: which, usage: COMMANDS[which].usage });
  } else {
    out.say(usageText());
    out.data({ commands: Object.fromEntries(Object.entries(COMMANDS).map(([k, v]) => [k, v.usage])) });
  }
  let session = null;
  try {
    const hit = requireSession(args.session, { project: findProjectRoot() });
    session = loadSession(hit.dir);
    context = { session, dir: hit.dir };
  } catch {
    context = { session: null, dir: null };
  }
  out.finish();
}

async function cmdVersion(args) {
  const out = new Out('version', args);
  let version = '1.0.0';
  try {
    version = JSON.parse(fs.readFileSync(path.join(REPO_ROOT, 'package.json'), 'utf8')).version || version;
  } catch {
    /* keep the default */
  }
  out.say(`ponder ${version}`);
  out.data({ version });
  out.finish({ phase: 'start', command: 'ponder help' });
}

const HANDLERS = {
  start: cmdStart,
  units: cmdUnits,
  predict: cmdPredict,
  grade: cmdGrade,
  deliberate: cmdDeliberate,
  delta: cmdDelta,
  judge: cmdJudge,
  decide: cmdDecide,
  status: cmdStatus,
  verify: cmdVerify,
  report: cmdReport,
  apply: cmdApply,
  list: cmdList,
  abort: cmdAbort,
  doctor: cmdDoctor,
  help: cmdHelp,
  version: cmdVersion,
};

// ---------------------------------------------------------------------------
// entry point
// ---------------------------------------------------------------------------

/**
 * Exit once stdout and stderr have actually drained.
 *
 * stdout on a pipe is asynchronous. `process.exit()` straight after a write throws away
 * whatever is still buffered, which truncates a large `--json` error payload at the 64 KB
 * pipe buffer and hands the caller invalid JSON — the failure mode that bites hardest is
 * `ponder delta --json | jq` on a batch with a few hundred problems in it.
 */
let exiting = false;
function exitWhenFlushed(code) {
  if (exiting) return;
  exiting = true;
  process.exitCode = code;
  let pending = 1;
  const done = () => {
    if (--pending === 0) process.exit(code);
  };
  for (const stream of [process.stdout, process.stderr]) {
    pending++;
    try {
      stream.write('', done);
    } catch {
      pending--; // a destroyed stream has nothing left to flush
    }
  }
  // A consumer that never reads must not hang the CLI for ever.
  const bail = setTimeout(() => process.exit(code), 10000);
  if (typeof bail.unref === 'function') bail.unref();
  done();
}

function fail(err, json) {
  // A closed pipe (`ponder status | head`) is not a ponder failure.
  if (err && (err.code === 'EPIPE' || err.code === 'ERR_STREAM_DESTROYED')) process.exit(0);
  const isPonder = err instanceof PonderError;
  const code = isPonder ? err.code : 1;
  const message = isPonder ? err.message : `${err && err.message ? err.message : String(err)}`;
  const detail = isPonder ? err.detail : [];
  // An argument error can fail before the session is resolved. Resolve it anyway, so the
  // NEXT line still names what this project owes rather than a generic "start a session".
  if (!context.session && commandName !== 'start') {
    try {
      const hit = requireSession(null, { project: findProjectRoot() });
      context = { session: loadSession(hit.dir), dir: hit.dir };
    } catch {
      /* no session to fall back to */
    }
  }
  const step = nextFor(context.session, { dir: context.dir });
  if (json) {
    process.stdout.write(JSON.stringify({ ok: false, error: message, detail, code, next: step }, null, 2) + '\n');
  } else {
    process.stderr.write(`${fmt.problem(message)}\n`);
    for (const line of detail) process.stderr.write(line === '' ? '\n' : `  ${line}\n`);
    if (!isPonder && process.env.PONDER_DEBUG) process.stderr.write(`${err && err.stack ? err.stack : ''}\n`);
    process.stdout.write(`\n${fmt.nextLine(step.phase, step.command)}\n`);
  }
  if (releaseLock) {
    releaseLock();
    releaseLock = null;
  }
  exitWhenFlushed(code);
}

async function main() {
  const argv = process.argv.slice(2);
  const wantsJson = argv.includes('--json');
  try {
    let name = argv[0];
    if (!name) {
      name = 'help';
    } else if (name.startsWith('-')) {
      const first = argv.shift();
      name = ['--version', '-v'].includes(first) ? 'version' : 'help';
    } else {
      argv.shift();
    }
    if (!HANDLERS[name]) {
      throw userError(`"${name}" is not a ponder command.`, [`commands: ${Object.keys(HANDLERS).join(', ')}`, 'try:  ponder help']);
    }
    commandName = name;
    ocaMode(); // validate PONDER_OCA once, for every command
    const spec = COMMANDS[name] || { flags: {}, usage: `ponder ${name}` };
    const args = parseArgs(argv, spec);
    if (args.help && name !== 'help') {
      await cmdHelp({ _: [name], json: args.json });
      return;
    }
    await HANDLERS[name](args);
  } catch (err) {
    fail(err, wantsJson);
  } finally {
    if (releaseLock) {
      releaseLock();
      releaseLock = null;
    }
  }
}

process.stdout.on('error', (err) => {
  if (err && err.code === 'EPIPE') process.exit(0);
});
process.on('uncaughtException', (err) => fail(err, process.argv.includes('--json')));
process.on('unhandledRejection', (err) => fail(err, process.argv.includes('--json')));

main();
