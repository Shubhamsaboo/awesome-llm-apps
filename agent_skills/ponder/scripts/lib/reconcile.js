// Ledger reconciliation: the ledger is the authority, the state files are a cache of it.
//
// SPEC 3.6. `units.json` and `findings.json` are convenient, indexed views of a session's
// state — but they are ordinary files, and an agent that wants past the coverage gate can
// simply edit them. `ledger.jsonl` is append-only and records every operation that has ever
// touched the session: the pass-1 inventory seed, the pass-1 finding seeding, and every
// delta after that. Nothing enters a session's state without leaving a ledger line, which
// means the honest state is independently reconstructible.
//
// This module replays the ledger from line 1, derives what units.json and findings.json
// must contain, and reports every place the files disagree with that derivation. The
// commands that draw a conclusion — judge, decide, report, apply — refuse to run on a
// session that does not reconcile.
//
// What it guarantees, and what it does not, is stated plainly in SPEC 3.6. In short: a
// forged state file is detected rather than believed. Someone who forges the ledger too is
// outside the model.

import { SETTABLE_FIELDS, UNIT_SETTABLE_FIELDS } from './deltas.js';
import { loadUnits, loadFindings, loadLedger, loadAllPassDeltas, stateError } from './session.js';

/** The ledger record that carries the pass-1 unit inventory. Not a delta — a seed. */
export const UNIT_SEED_OP = 'unit-seed';

/**
 * Finding fields the ledger pins.
 *
 * Every settable field, because an `add` record carries the whole normalised finding body
 * and every later `edit` / `change` carries the exact `set` that was applied — so replay
 * reproduces the field values byte for byte. Plus `createdInPass`, which is the pass of the
 * `add` record itself.
 *
 * Deliberately excluded: `lastTouchedPass` and `history`. The ledger implies both, but they
 * are engine bookkeeping — a disagreement there cannot buy a forger coverage, a finding, or
 * a line in the apply plan, and pinning derived presentation is how a reconciler starts
 * crying wolf. `id` is not a field here; it is the key everything else is compared under.
 */
export const FINDING_PINNED = [...SETTABLE_FIELDS, 'createdInPass'];

/**
 * Unit fields the ledger pins.
 *
 * The body fields come from the `unit-seed` record (pass 1) or a `unit-add` record (later
 * passes), both of which carry the unit exactly as it was stored. `path` is in the list
 * because it is not decoration: a phantom claim is checked against it, so a unit that
 * quietly loses its path is a unit whose phantom claim nobody can check.
 *
 * The removal fields come from `unit-delete`. They are the ones the coverage denominator is
 * computed from, which is what this whole mechanism exists to protect.
 */
export const UNIT_PINNED = [
  'label',
  'path',
  'kind',
  'meta',
  'addedInPass',
  'removedInPass',
  'removalKind',
  'phantomVerification',
  'phantomPath',
];

/** Absent and null are the same claim: "this field says nothing". */
const norm = (v) => (v === undefined ? null : v);
const same = (a, b) => JSON.stringify(norm(a)) === JSON.stringify(norm(b));

/** Render a value for a diagnosis line. `(unset)` is not the same as the string "null". */
function show(v) {
  if (v === undefined || v === null) return '(unset)';
  const text = typeof v === 'string' ? JSON.stringify(v) : JSON.stringify(v);
  return text.length > 90 ? `${text.slice(0, 87)}…` : text;
}

const pick = (source, fields) => {
  const out = {};
  for (const f of fields) out[f] = norm(source ? source[f] : undefined);
  return out;
};

// ---------------------------------------------------------------------------
// replay
// ---------------------------------------------------------------------------

/**
 * Replay the ledger and derive the state it describes.
 *
 * Returns `{ findings, units, ledgerProblems, counts }`, where findings and units are Maps
 * keyed by id holding only the pinned fields. `ledgerProblems` are contradictions *inside*
 * the ledger — a delta against an id no earlier record created. Those are not forgeries of
 * a state file; they are a ledger that does not describe a reachable session, and they are
 * reported separately so the diagnosis says which kind of problem it found.
 */
export function replayLedger(ledger) {
  const findings = new Map();
  const units = new Map();
  const ledgerProblems = [];
  const counts = { records: 0, seeds: 0, adds: 0, unitAdds: 0, unitEdits: 0, unitDeletes: 0, revisions: 0 };

  const complain = (line, message) => ledgerProblems.push({ line, message });

  let line = 0;
  for (const rec of ledger) {
    line++;
    if (!rec || typeof rec !== 'object' || Array.isArray(rec)) {
      complain(line, 'a ledger record that is not a JSON object.');
      continue;
    }
    counts.records++;
    const op = rec.op;
    const pass = rec.pass === undefined || rec.pass === null ? null : Number(rec.pass);

    if (op === UNIT_SEED_OP) {
      counts.seeds++;
      const seeded = Array.isArray(rec.units) ? rec.units : [];
      const declared = Array.isArray(rec.ids) ? rec.ids : null;
      for (const u of seeded) {
        if (!u || typeof u.id !== 'string') {
          complain(line, 'the unit-seed record carries a unit with no string id.');
          continue;
        }
        units.set(u.id, pick(u, UNIT_PINNED));
      }
      // `ids` is the record's own summary of `units`. If the two disagree, the ledger
      // contradicts itself, and saying so is more useful than silently trusting one.
      if (declared) {
        const fromBodies = seeded.filter((u) => u && typeof u.id === 'string').map((u) => u.id);
        if (JSON.stringify(declared) !== JSON.stringify(fromBodies)) {
          complain(line, `the unit-seed record's "ids" (${declared.length}) do not match its "units" (${fromBodies.length}).`);
        }
      }
      continue;
    }

    if (op === 'unit-add') {
      counts.unitAdds++;
      counts.revisions++;
      const u = rec.unit;
      if (!u || typeof u.id !== 'string') {
        complain(line, 'a unit-add record with no unit id.');
        continue;
      }
      units.set(u.id, pick(u, UNIT_PINNED));
      continue;
    }

    if (op === 'unit-edit') {
      counts.unitEdits++;
      counts.revisions++;
      const id = rec.target;
      const u = typeof id === 'string' ? units.get(id) : null;
      if (!u) {
        complain(line, `unit-edit targets "${id}", which no earlier record enumerated.`);
        continue;
      }
      const set = rec.set;
      if (!set || typeof set !== 'object' || Array.isArray(set)) {
        complain(line, `unit-edit on "${id}" carries no "set" object.`);
        continue;
      }
      for (const [field, value] of Object.entries(set)) {
        if (!UNIT_SETTABLE_FIELDS.includes(field)) {
          // `applyDeltas` builds a unit-edit record's `set` out of validated fields only, so
          // the engine can never have written this line — `id` above all, which it refuses
          // by name because it is the join key to findings.json. Skipping it silently made
          // a forgery cheaper than the three-file bar SPEC 3.6 sets: a replay ignores the
          // field, so ledger.jsonl and passes/NN/deltas.jsonl alone carried the lie, no
          // state file had to be touched, and `report.md` printed the correction as fact.
          complain(
            line,
            `unit-edit on "${id}" sets "${field}", which is not a settable unit field (${UNIT_SETTABLE_FIELDS.join(', ')}) — the engine refuses to write that record, so this ledger is not one it wrote.`,
          );
          continue;
        }
        // meta merges key by key, exactly as the engine applied it (SPEC 3.4). Replaying it
        // as a wholesale replace would derive a state the engine never wrote, and every
        // honest session that ever corrected a route would stop reconciling.
        if (field === 'meta') {
          const base = u.meta && typeof u.meta === 'object' && !Array.isArray(u.meta) ? u.meta : {};
          u.meta = { ...base, ...(value && typeof value === 'object' && !Array.isArray(value) ? value : {}) };
          continue;
        }
        u[field] = norm(value);
      }
      continue;
    }

    if (op === 'unit-delete') {
      counts.unitDeletes++;
      counts.revisions++;
      const id = rec.target;
      const u = typeof id === 'string' ? units.get(id) : null;
      if (!u) {
        complain(line, `unit-delete targets "${id}", which no earlier record enumerated.`);
        continue;
      }
      u.removedInPass = pass;
      u.removalKind = norm(rec.removal);
      if (rec.removal === 'phantom') {
        u.phantomVerification = rec.verification === undefined ? 'unverified' : rec.verification;
        u.phantomPath = norm(rec.verifiedPath);
      }
      continue;
    }

    if (op === 'add') {
      counts.adds++;
      if (rec.source !== 'grade') counts.revisions++;
      const id = rec.id ?? rec.target;
      if (typeof id !== 'string' || id === '') {
        complain(line, 'an add record with no engine-assigned finding id.');
        continue;
      }
      if (findings.has(id)) complain(line, `a second add record for "${id}" — finding ids are never reused.`);
      const body = rec.finding && typeof rec.finding === 'object' ? rec.finding : {};
      const f = pick(body, SETTABLE_FIELDS);
      f.createdInPass = pass;
      findings.set(id, f);
      continue;
    }

    if (op === 'delete' || op === 'edit' || op === 'change') {
      counts.revisions++;
      const id = rec.target;
      const f = typeof id === 'string' ? findings.get(id) : null;
      if (!f) {
        complain(line, `${op} targets "${id}", which no earlier add record created.`);
        continue;
      }
      if (op === 'delete') {
        f.status = 'retracted';
        continue;
      }
      const set = rec.set;
      if (!set || typeof set !== 'object' || Array.isArray(set)) {
        complain(line, `${op} on "${id}" carries no "set" object.`);
        continue;
      }
      for (const [field, value] of Object.entries(set)) {
        if (SETTABLE_FIELDS.includes(field)) f[field] = norm(value);
      }
      continue;
    }

    complain(line, `unknown ledger op ${JSON.stringify(op)}.`);
  }

  return { findings, units, ledgerProblems, counts };
}

// ---------------------------------------------------------------------------
// the union invariant
// ---------------------------------------------------------------------------

/** A record's own claim about which pass it belongs to. `null` when it does not make one. */
const passOf = (rec) => {
  const p = rec && typeof rec === 'object' ? rec.pass : undefined;
  return p === undefined || p === null || !Number.isFinite(Number(p)) ? null : Number(p);
};

/** Canonical form for comparing two records that should be the same record. */
const canon = (rec) => JSON.stringify(rec);

/**
 * Check the ledger against the per-pass delta files.
 *
 * SPEC 3.4: "`ledger.jsonl` is the union of all passes' `deltas.jsonl`, never rewritten."
 * `recordDeltas` writes both in one call, so this is exact — the same records, in the same
 * order, grouped by pass. That makes the per-pass files an independent second copy of the
 * ledger, and it is why reconciliation is not defeated by appending one plausible line to
 * `ledger.jsonl`: the line has to appear in `passes/NN/deltas.jsonl` too, at the same
 * position, or the two copies disagree and say so.
 *
 * It also catches what a pure replay cannot: reordering `ledger.jsonl` (a rewrite of an
 * append-only file, and a way to change what replay derives without writing a new record),
 * truncating it, and deleting a pass directory out from under it.
 *
 * Returns `[{ pass, message }]`, empty when the two copies agree.
 */
export function checkUnion(ledger, passDeltas) {
  const problems = [];
  const say = (pass, message) => problems.push({ pass, message });
  if (!Array.isArray(passDeltas)) return problems;

  // Group the ledger by each record's own `pass`, preserving ledger order within a group.
  const byPass = new Map();
  let unpassed = 0;
  ledger.forEach((rec, i) => {
    const p = passOf(rec);
    if (p === null) {
      unpassed++;
      if (unpassed === 1) say(null, `ledger.jsonl line ${i + 1} carries no pass number, so no pass's deltas.jsonl can account for it.`);
      return;
    }
    if (!byPass.has(p)) byPass.set(p, []);
    byPass.get(p).push({ rec, line: i + 1 });
  });
  if (unpassed > 1) say(null, `${unpassed} ledger.jsonl lines in total carry no pass number.`);

  // The ledger's own pass sequence must never go backwards: it is appended to as the loop
  // runs, and the loop only ever moves forward.
  let high = -Infinity;
  for (const rec of ledger) {
    const p = passOf(rec);
    if (p === null) continue;
    if (p < high) {
      say(p, `ledger.jsonl records go backwards in pass order (a pass ${high} record is followed by a pass ${p} record). The ledger is appended to as the loop runs and is never rewritten (SPEC 3.4).`);
      break;
    }
    high = p;
  }

  const passes = [...new Set([...byPass.keys(), ...passDeltas.map((p) => p.pass)])].sort((a, b) => a - b);
  const onDisk = new Map(passDeltas.map((p) => [p.pass, p]));

  for (const pass of passes) {
    const nn = String(pass).padStart(2, '0');
    const file = `passes/${nn}/deltas.jsonl`;
    const fromLedger = byPass.get(pass) || [];
    const entry = onDisk.get(pass);

    if (!entry || !entry.present) {
      if (fromLedger.length) {
        say(pass, `the ledger carries ${plural(fromLedger.length, 'record')} for pass ${pass}, and ${file} is missing. The ledger is the union of the per-pass delta files (SPEC 3.4), so a pass cannot lose its half of the record.`);
      }
      continue;
    }
    const fromFile = entry.records;
    if (!fromLedger.length && fromFile.length) {
      say(pass, `${file} holds ${plural(fromFile.length, 'record')} that ledger.jsonl has none of for pass ${pass}.`);
      continue;
    }

    const n = Math.max(fromLedger.length, fromFile.length);
    for (let i = 0; i < n; i++) {
      const l = fromLedger[i];
      const f = fromFile[i];
      if (l && !f) {
        say(pass, `ledger.jsonl line ${l.line} is a pass-${pass} record that ${file} does not have (the ledger has ${fromLedger.length} for this pass, the file has ${fromFile.length}).`);
        break;
      }
      if (!l && f) {
        say(pass, `${file} line ${i + 1} is a record ledger.jsonl does not carry (the file has ${fromFile.length} for this pass, the ledger has ${fromLedger.length}).`);
        break;
      }
      if (canon(l.rec) !== canon(f)) {
        say(pass, `ledger.jsonl line ${l.line} and ${file} line ${i + 1} are both the ${ordinal(i + 1)} record of pass ${pass}, and they are not the same record. The ledger says ${show(l.rec.op)} on ${show(l.rec.target ?? l.rec.id ?? null)}, the file says ${show(f && f.op)} on ${show((f && (f.target ?? f.id)) ?? null)}.`);
        break;
      }
    }
  }
  return problems;
}

const ordinal = (n) => {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
};

// ---------------------------------------------------------------------------
// comparison
// ---------------------------------------------------------------------------

/** Index a state array by id, reporting entries with no id and ids that repeat. */
function indexById(rows, scope, divergences, file) {
  const map = new Map();
  rows.forEach((row, i) => {
    const id = row && typeof row.id === 'string' && row.id !== '' ? row.id : null;
    if (id === null) {
      divergences.push({
        kind: `${scope}-unidentified`,
        scope,
        id: `${file} entry ${i + 1}`,
        message: `${scope} entry ${i + 1} in ${file} has no id, so nothing in the ledger can account for it.`,
      });
      return;
    }
    if (map.has(id)) {
      divergences.push({
        kind: `${scope}-duplicate`,
        scope,
        id,
        message: `${scope} ${id} appears more than once in ${file}; the ledger created it once.`,
      });
      return;
    }
    map.set(id, row);
  });
  return map;
}

function compareSet({ scope, file, expected, actual, fields, divergences, labels }) {
  const ids = [...new Set([...expected.keys(), ...actual.keys()])].sort();
  for (const id of ids) {
    const want = expected.get(id);
    const got = actual.get(id);
    if (want && !got) {
      divergences.push({ kind: `${scope}-missing`, scope, id, message: labels.missing(id) });
      continue;
    }
    if (!want && got) {
      divergences.push({ kind: `${scope}-unledgered`, scope, id, message: labels.unledgered(id) });
      continue;
    }
    for (const field of fields) {
      if (same(want[field], got[field])) continue;
      divergences.push({
        kind: `${scope}-field`,
        scope,
        id,
        field,
        ledger: norm(want[field]),
        file: norm(got[field]),
        message: `${scope} ${id}.${field} — the ledger says ${show(want[field])}, ${file} says ${show(got[field])}.`,
      });
    }
  }
}

// ---------------------------------------------------------------------------
// full derivation — what `verify --repair` rebuilds from
// ---------------------------------------------------------------------------

/**
 * Replay the ledger into complete `units` and `findings` arrays.
 *
 * `replayLedger` above derives only the fields reconciliation pins, which is all a
 * comparison needs. Repair needs the whole document, bookkeeping included, so this second
 * replay reproduces exactly what `applyDeltas` would have written: field order, the derived
 * `lastTouchedPass`, and each finding's `history` of what changed when.
 *
 * The two replays are deliberately separate. The comparison must stay narrow — pinning
 * derived presentation is how a reconciler starts crying wolf (SPEC 3.6) — while a rebuild
 * must be total, because a state file missing its bookkeeping is not the file the engine
 * would have written.
 */
export function deriveState(ledger) {
  const units = [];
  const findings = [];
  const unitById = new Map();
  const findingById = new Map();

  for (const rec of Array.isArray(ledger) ? ledger : []) {
    if (!rec || typeof rec !== 'object' || Array.isArray(rec)) continue;
    const pass = rec.pass === undefined || rec.pass === null ? null : Number(rec.pass);
    const op = rec.op;

    if (op === UNIT_SEED_OP) {
      for (const u of Array.isArray(rec.units) ? rec.units : []) {
        if (!u || typeof u.id !== 'string' || unitById.has(u.id)) continue;
        const copy = { ...u };
        units.push(copy);
        unitById.set(u.id, copy);
      }
      continue;
    }

    if (op === 'unit-add') {
      const u = rec.unit;
      if (!u || typeof u.id !== 'string' || unitById.has(u.id)) continue;
      const copy = { ...u };
      units.push(copy);
      unitById.set(u.id, copy);
      continue;
    }

    if (op === 'unit-edit') {
      const u = unitById.get(rec.target);
      if (!u || !rec.set || typeof rec.set !== 'object') continue;
      for (const [field, value] of Object.entries(rec.set)) {
        if (!UNIT_SETTABLE_FIELDS.includes(field)) continue;
        if (field === 'meta') {
          const base = u.meta && typeof u.meta === 'object' && !Array.isArray(u.meta) ? u.meta : {};
          u.meta = { ...base, ...(value && typeof value === 'object' && !Array.isArray(value) ? value : {}) };
          continue;
        }
        u[field] = value;
      }
      continue;
    }

    if (op === 'unit-delete') {
      const u = unitById.get(rec.target);
      if (!u) continue;
      u.removedInPass = pass;
      u.removalKind = rec.removal ?? null;
      if (rec.removal === 'phantom') {
        u.phantomVerification = rec.verification === undefined ? 'unverified' : rec.verification;
        u.phantomPath = rec.verifiedPath === undefined ? null : rec.verifiedPath;
      }
      continue;
    }

    if (op === 'add') {
      const id = rec.id ?? rec.target;
      if (typeof id !== 'string' || id === '' || findingById.has(id)) continue;
      const body = rec.finding && typeof rec.finding === 'object' ? rec.finding : {};
      // Same field order normaliseFinding writes, so a rebuilt findings.json is the file
      // the engine would have written, byte for byte.
      const f = {
        id,
        unit: body.unit,
        title: body.title,
        detail: body.detail,
        dimension: body.dimension === undefined ? null : body.dimension,
        score: body.score,
        severity: body.severity,
        confidence: body.confidence,
        effort: body.effort,
        evidence: body.evidence === undefined ? [] : body.evidence,
        recommendation: body.recommendation,
        status: body.status,
        createdInPass: pass,
        lastTouchedPass: pass,
        history: [],
      };
      findings.push(f);
      findingById.set(id, f);
      continue;
    }

    if (op === 'delete') {
      const f = findingById.get(rec.target);
      if (!f) continue;
      f.history.push({ pass, op: 'delete', field: 'status', from: f.status, to: 'retracted' });
      f.status = 'retracted';
      f.lastTouchedPass = pass;
      continue;
    }

    if (op === 'edit' || op === 'change') {
      const f = findingById.get(rec.target);
      if (!f || !rec.set || typeof rec.set !== 'object') continue;
      for (const [field, value] of Object.entries(rec.set)) {
        if (!SETTABLE_FIELDS.includes(field)) continue;
        const from = f[field];
        if (JSON.stringify(from) === JSON.stringify(value)) continue;
        f.history.push({ pass, op, field, from: from === undefined ? null : from, to: value });
        f[field] = value;
      }
      f.lastTouchedPass = pass;
      continue;
    }
  }

  return { units, findings };
}

/**
 * Split a set of divergences into what the ledger can rebuild and what it cannot.
 *
 * SPEC 3.6 makes the ledger the authority, and that asymmetry is the whole reason
 * `ponder verify --repair` exists. A **ledger-ahead** session — the ledger holds records the
 * state files have not caught up to — is fully recoverable: replay derives the state those
 * records must have produced, and writing it out is deterministic. A **state-ahead**
 * session — a state file holds a unit or a finding no ledger record ever created — is not:
 * that data exists nowhere else, so there is nothing to rebuild it from, and it is either a
 * forgery or an unrecoverable loss. Repair fixes the first and refuses the second.
 */
export function classifyDivergences(divergences) {
  const repairable = [];
  const unrecoverable = [];
  for (const d of divergences) {
    if (d.kind === 'unit-missing' || d.kind === 'finding-missing' || d.kind === 'unit-field' || d.kind === 'finding-field') {
      repairable.push(d);
    } else {
      unrecoverable.push(d);
    }
  }
  return { repairable, unrecoverable };
}

/**
 * Work out how to bring the per-pass `deltas.jsonl` files back up to the ledger.
 *
 * `recordDeltas` appends to `ledger.jsonl` first and to `passes/NN/deltas.jsonl` second
 * (SPEC 3.6), so the only crash window between them leaves a pass file holding a **prefix**
 * of what the ledger has for that pass. That is repairable: append the tail. Anything else —
 * a pass file holding a record the ledger does not, or the same position holding two
 * different records — is not a lag, it is a disagreement between two copies of an
 * append-only log, and repair refuses it.
 *
 * Returns `{ appends: [{ pass, records }], problems: [] }`.
 */
export function planUnionRepair(ledger, passDeltas) {
  const appends = [];
  const problems = [];
  const byPass = new Map();
  for (const rec of Array.isArray(ledger) ? ledger : []) {
    const p = passOf(rec);
    if (p === null) {
      problems.push({ pass: null, message: 'a ledger record carries no pass number, so no pass file can be brought up to it.' });
      continue;
    }
    if (!byPass.has(p)) byPass.set(p, []);
    byPass.get(p).push(rec);
  }
  const onDisk = new Map((Array.isArray(passDeltas) ? passDeltas : []).map((p) => [p.pass, p]));
  const passes = [...new Set([...byPass.keys(), ...onDisk.keys()])].sort((a, b) => a - b);

  for (const pass of passes) {
    const want = byPass.get(pass) || [];
    const entry = onDisk.get(pass);
    const have = entry && entry.present ? entry.records : [];
    if (have.length > want.length) {
      problems.push({
        pass,
        message: `passes/${String(pass).padStart(2, '0')}/deltas.jsonl holds ${plural(have.length, 'record')} and ledger.jsonl holds ${want.length} for pass ${pass}. The pass file is ahead of the ledger, so the ledger is not the authority here and repair cannot derive the missing records from it.`,
      });
      continue;
    }
    let diverged = false;
    for (let i = 0; i < have.length; i++) {
      if (canon(have[i]) !== canon(want[i])) {
        problems.push({
          pass,
          message: `passes/${String(pass).padStart(2, '0')}/deltas.jsonl line ${i + 1} is not the record ledger.jsonl carries at that position. The two copies disagree rather than one lagging, so repair refuses to overwrite either.`,
        });
        diverged = true;
        break;
      }
    }
    if (diverged) continue;
    if (want.length > have.length) appends.push({ pass, records: want.slice(have.length) });
  }
  return { appends, problems };
}

/**
 * Reconcile a session's state files against its ledger.
 *
 * Pure: everything it needs is the three documents. Returns
 * `{ ok, divergences, ledgerProblems, counts }`.
 */
export function reconcile({ ledger = [], units = [], findings = [], passDeltas = [], skippedLedgerLines = [] } = {}) {
  const derived = replayLedger(ledger);
  const unionProblems = checkUnion(ledger, passDeltas);
  const divergences = [];

  const actualUnits = indexById(units, 'unit', divergences, 'units.json');
  const actualFindings = indexById(findings, 'finding', divergences, 'findings.json');

  compareSet({
    scope: 'unit',
    file: 'units.json',
    expected: derived.units,
    actual: actualUnits,
    fields: UNIT_PINNED,
    divergences,
    labels: {
      missing: (id) => `unit ${id} — the ledger enumerated it, units.json does not have it. A unit cannot leave the inventory by being deleted from the file; it leaves with a unit-delete delta, on the record.`,
      unledgered: (id) => `unit ${id} — units.json has it, no ledger record ever enumerated it.`,
    },
  });

  compareSet({
    scope: 'finding',
    file: 'findings.json',
    expected: derived.findings,
    actual: actualFindings,
    fields: FINDING_PINNED,
    divergences,
    labels: {
      missing: (id) => `finding ${id} — the ledger created it, findings.json does not have it. Nothing is ever removed from findings.json (SPEC 8.2); retraction is a status, not an erasure.`,
      unledgered: (id) => `finding ${id} — findings.json has it, no ledger record ever created it.`,
    },
  });

  // Units first, then findings; within each, by id. A stable order means two runs of
  // `ponder verify` on the same session read identically.
  const order = { unit: 0, finding: 1 };
  divergences.sort((a, b) => (order[a.scope] - order[b.scope]) || String(a.id).localeCompare(String(b.id)) || String(a.field || '').localeCompare(String(b.field || '')));

  return {
    ok: divergences.length === 0 && derived.ledgerProblems.length === 0 && unionProblems.length === 0,
    divergences,
    ledgerProblems: derived.ledgerProblems,
    unionProblems,
    skippedLedgerLines,
    counts: {
      ...derived.counts,
      expectedUnits: derived.units.size,
      actualUnits: units.length,
      expectedFindings: derived.findings.size,
      actualFindings: findings.length,
      passFiles: Array.isArray(passDeltas) ? passDeltas.length : 0,
      passRecords: Array.isArray(passDeltas) ? passDeltas.reduce((n, p) => n + p.records.length, 0) : 0,
    },
  };
}

/** Reconcile the session in `dir`, reading its documents off disk. */
export function reconcileAt(dir) {
  const skipped = [];
  const ledger = loadLedger(dir, { skipped });
  return reconcile({
    ledger,
    units: loadUnits(dir).units,
    findings: loadFindings(dir).findings,
    passDeltas: loadAllPassDeltas(dir),
    skippedLedgerLines: skipped,
  });
}

// ---------------------------------------------------------------------------
// diagnosis
// ---------------------------------------------------------------------------

const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

/** The detail block printed on a refusal and by `ponder verify`. */
export function diagnose(result, { slug = null, limit = 24 } = {}) {
  const lines = [];
  lines.push('ledger.jsonl is the authority: it records every operation this session ever applied,');
  lines.push('and it is append-only. units.json and findings.json are a view of it, and the per-pass');
  lines.push('deltas.jsonl files are a second copy of it, so where either disagrees with the ledger,');
  lines.push('that is the side that is wrong.');
  if (result.divergences.length) {
    lines.push('');
    lines.push(`${plural(result.divergences.length, 'divergence')}:`);
    for (const d of result.divergences.slice(0, limit)) lines.push(`  ${d.message}`);
    if (result.divergences.length > limit) {
      lines.push(`  … and ${result.divergences.length - limit} more.`);
    }
  }
  if (result.ledgerProblems.length) {
    lines.push('');
    lines.push(`${plural(result.ledgerProblems.length, 'problem')} inside ledger.jsonl itself:`);
    for (const p of result.ledgerProblems.slice(0, limit)) lines.push(`  line ${p.line}: ${p.message}`);
    if (result.ledgerProblems.length > limit) {
      lines.push(`  … and ${result.ledgerProblems.length - limit} more.`);
    }
  }
  const union = result.unionProblems || [];
  if (union.length) {
    lines.push('');
    lines.push(`ledger.jsonl and the per-pass delta files are two copies of the same records`);
    lines.push(`(SPEC 3.4), and they disagree in ${plural(union.length, 'place')}:`);
    for (const p of union.slice(0, limit)) lines.push(`  ${p.message}`);
    if (union.length > limit) lines.push(`  … and ${union.length - limit} more.`);
  }
  if (result.skippedLedgerLines && result.skippedLedgerLines.length) {
    lines.push('');
    lines.push(
      `${plural(result.skippedLedgerLines.length, 'line')} of ledger.jsonl (${result.skippedLedgerLines.map((s) => s.line).join(', ')}) could not be parsed and were left out of the replay.`,
    );
    lines.push('A divergence above may be that torn write rather than an edit. Repair those lines first.');
  }
  lines.push('');
  lines.push(`run:  ponder verify${slug ? ` --session ${slug}` : ''}`);
  return lines;
}

/** Throw the exit-2 refusal a decision point owes when a session does not reconcile. */
export function requireReconciled(result, { slug, command }) {
  if (result.ok) return result;
  const n = result.divergences.length + result.ledgerProblems.length + (result.unionProblems || []).length;
  throw stateError(
    `session ${slug} does not reconcile with its ledger — ${plural(n, 'divergence')}. "ponder ${command}" draws a conclusion from this state, so it is refused.`,
    diagnose(result, { slug }),
  );
}
