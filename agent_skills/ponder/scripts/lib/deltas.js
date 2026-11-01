// Deltas: the only way the finding set ever changes after it is seeded.
//
// A delta is one JSON object per line (SPEC 3.4). Validation and application run together
// against a cloned state so that a file with a bad line on line 40 changes nothing at all:
// either every delta in the batch applies, or none does.

import fs from 'node:fs';
import path from 'node:path';

import { userError } from './session.js';

export const OPS = ['add', 'edit', 'change', 'delete', 'unit-add', 'unit-edit', 'unit-delete'];

/**
 * How a unit left the inventory (SPEC 3.2, SPEC 4).
 *
 *  appraised        — the unit carried at least one finding, so dropping it is an honest
 *                     scope change and the coverage denominator shrinks.
 *  removed-ungraded — the unit was never graded and no phantom claim was made. It stays in
 *                     the denominator: a delete cannot manufacture coverage.
 *  phantom          — the unit does not exist in the software; pass 1 enumerated it wrongly.
 *                     Verified by the engine where a path allows it, then dropped.
 */
export const REMOVAL_KINDS = ['appraised', 'removed-ungraded', 'phantom'];
export const PHANTOM_VERIFICATIONS = ['verified-missing', 'unverified'];
export const PERSPECTIVES = ['skeptic', 'builder', 'dreamer', 'empath'];
export const SEVERITIES = ['must', 'should', 'could', 'note'];
export const EFFORTS = ['xs', 's', 'm', 'l', 'xl'];
export const FINDING_STATUSES = ['open', 'resolved', 'retracted', 'deferred'];

/** Fields a delta may set on a finding. Everything else is engine bookkeeping. */
export const SETTABLE_FIELDS = [
  'unit',
  'title',
  'detail',
  'dimension',
  'score',
  'severity',
  'confidence',
  'effort',
  'evidence',
  'recommendation',
  'status',
];

/**
 * Fields a `unit-edit` may set on a unit (SPEC 3.4).
 *
 * `id` is deliberately absent and is rejected by name rather than by falling through to
 * "unknown field": it is the join key between units.json and findings.json, so changing it
 * would orphan every finding hanging off that unit.
 */
export const UNIT_SETTABLE_FIELDS = ['label', 'path', 'kind', 'meta'];

/** Fields `change` is meant for; the rest are `edit` territory. Advisory only (SPEC 3.4). */
export const GRADE_FIELDS = ['score', 'severity', 'confidence', 'effort', 'status'];

export const SEVERITY_RANK = { must: 0, should: 1, could: 2, note: 3 };
export const EFFORT_RANK = { xs: 0, s: 1, m: 2, l: 3, xl: 4 };

const UNIT_ID_RE = /^[a-z0-9]+([._-][a-z0-9]+)*$/;

const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

/** Parse a deltas.jsonl payload into [{ delta, line }]; blank lines are ignored. */
export function parseDeltaSource(text, { label = 'deltas' } = {}) {
  const trimmed = String(text ?? '').trim();
  const out = [];
  if (trimmed === '') return out;

  // Tolerate a JSON array as well as JSONL — agents produce both.
  if (trimmed.startsWith('[')) {
    let arr;
    try {
      arr = JSON.parse(trimmed);
    } catch (err) {
      throw userError(`${label} is not valid JSON: ${err.message}`);
    }
    if (!Array.isArray(arr)) throw userError(`${label} must be a JSON array or one JSON object per line.`);
    arr.forEach((delta, i) => out.push({ delta, line: i + 1 }));
    return out;
  }

  const lines = String(text).split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line === '') continue;
    let delta;
    try {
      delta = JSON.parse(line);
    } catch (err) {
      throw userError(`${label} line ${i + 1} is not valid JSON: ${err.message}`);
    }
    out.push({ delta, line: i + 1 });
  }
  return out;
}

export function nextFindingId(findings) {
  let max = 0;
  for (const f of findings) {
    const m = /^f-(\d+)$/.exec(String(f.id ?? ''));
    if (m) max = Math.max(max, Number(m[1]));
  }
  return (n = 1) => `f-${String(max + n).padStart(4, '0')}`;
}

// ---------------------------------------------------------------------------
// field validation
// ---------------------------------------------------------------------------

function checkField(field, value, errs, where) {
  const bad = (msg) => errs.push(`${where}: ${msg}`);
  switch (field) {
    case 'unit':
      if (typeof value !== 'string' || value.trim() === '') bad('unit must be a non-empty string.');
      break;
    case 'title':
      if (typeof value !== 'string' || value.trim() === '') bad('title must be a non-empty string.');
      break;
    case 'detail':
    case 'recommendation':
      if (typeof value !== 'string') bad(`${field} must be a string.`);
      break;
    case 'dimension':
      if (value !== null && (typeof value !== 'string' || value.trim() === ''))
        bad('dimension must be a non-empty string or null.');
      break;
    case 'score':
      if (!Number.isInteger(value) || value < 1 || value > 5) bad('score must be an integer 1-5.');
      break;
    case 'severity':
      if (!SEVERITIES.includes(value)) bad(`severity must be one of ${SEVERITIES.join(', ')}.`);
      break;
    case 'confidence':
      if (typeof value !== 'number' || Number.isNaN(value) || value < 0 || value > 1)
        bad('confidence must be a number between 0 and 1.');
      break;
    case 'effort':
      if (!EFFORTS.includes(value)) bad(`effort must be one of ${EFFORTS.join(', ')}.`);
      break;
    case 'evidence':
      if (!Array.isArray(value) || value.some((e) => typeof e !== 'string'))
        bad('evidence must be an array of strings.');
      break;
    case 'status':
      if (!FINDING_STATUSES.includes(value)) bad(`status must be one of ${FINDING_STATUSES.join(', ')}.`);
      break;
    default:
      bad(`"${field}" is not a settable finding field (${SETTABLE_FIELDS.join(', ')}).`);
  }
}

/** Fill a raw finding with defaults and validate it. Returns the normalised object. */
export function normaliseFinding(raw, { pass, id, errs, where }) {
  const f = raw && typeof raw === 'object' && !Array.isArray(raw) ? raw : {};
  if (raw === null || typeof raw !== 'object' || Array.isArray(raw)) {
    errs.push(`${where}: "finding" must be an object.`);
    return null;
  }
  if (f.id !== undefined && f.id !== null) {
    errs.push(`${where}: an "add" carries a finding without an id — the engine assigns it (got "${f.id}").`);
  }
  for (const required of ['unit', 'title', 'score', 'severity']) {
    if (f[required] === undefined) errs.push(`${where}: finding is missing required field "${required}".`);
  }
  const evidence = f.evidence === undefined ? [] : typeof f.evidence === 'string' ? [f.evidence] : f.evidence;
  const out = {
    id,
    unit: f.unit,
    title: typeof f.title === 'string' ? f.title.trim() : f.title,
    detail: f.detail === undefined ? '' : f.detail,
    dimension: f.dimension === undefined ? null : f.dimension,
    score: f.score,
    severity: f.severity,
    confidence: f.confidence === undefined ? 0.5 : f.confidence,
    effort: f.effort === undefined ? 'm' : f.effort,
    evidence,
    recommendation: f.recommendation === undefined ? '' : f.recommendation,
    status: f.status === undefined ? 'open' : f.status,
    createdInPass: pass,
    lastTouchedPass: pass,
    history: [],
  };
  for (const field of SETTABLE_FIELDS) {
    if (out[field] !== undefined) checkField(field, out[field], errs, where);
  }
  for (const key of Object.keys(f)) {
    if (!SETTABLE_FIELDS.includes(key) && !['id', 'createdInPass', 'lastTouchedPass', 'history'].includes(key)) {
      errs.push(`${where}: unknown finding field "${key}".`);
    }
  }
  return out;
}

/** Validate one field of a `unit-edit` set. Mirrors checkField, for units. */
function checkUnitField(field, value, errs, where, id) {
  const bad = (msg) => errs.push(`${where}: ${msg}`);
  switch (field) {
    case 'label':
      if (typeof value !== 'string' || value.trim() === '') bad(`unit "${id}" label must be a non-empty string.`);
      break;
    case 'path':
      // null is a legal value: it clears the evidence anchor. It does not clear the
      // *history* of the anchor, which is what a phantom claim is checked against (3.5).
      if (value !== null && (typeof value !== 'string' || value.trim() === ''))
        bad(`unit "${id}" path must be a non-empty string or null.`);
      break;
    case 'kind':
      if (value !== null && (typeof value !== 'string' || value.trim() === ''))
        bad(`unit "${id}" kind must be a non-empty string or null.`);
      break;
    case 'meta':
      if (value === null || typeof value !== 'object' || Array.isArray(value))
        bad(`unit "${id}" meta must be an object — it merges key by key, so null cannot say what to merge.`);
      break;
    default:
      bad(`"${field}" is not a settable unit field (${UNIT_SETTABLE_FIELDS.join(', ')}).`);
  }
}

/**
 * Every path a unit has ever carried, read off the ledger, oldest first.
 *
 * This is what a phantom claim is checked against (SPEC 3.5). `unit-edit` can move a
 * unit's `path`, and a claim checked against only the current value would let an agent
 * point a real unit at a filename that does not exist and then certify it away — the
 * coverage gate defeated in two deltas. So the check runs against the original path from
 * the `unit-seed` or `unit-add` record plus every value any `unit-edit` has set since.
 *
 * Returns a Map of unit id → [{ path, pass, source }], where `path` is null for a record
 * that carried no path (or cleared it) and `source` is the op that set it.
 */
export function unitPathHistory(ledger) {
  const map = new Map();
  const push = (id, value, pass, source) => {
    if (typeof id !== 'string' || id === '') return;
    if (!map.has(id)) map.set(id, []);
    map.get(id).push({
      path: typeof value === 'string' && value.trim() !== '' ? value.trim() : null,
      pass: Number.isFinite(Number(pass)) ? Number(pass) : null,
      source,
    });
  };
  for (const rec of Array.isArray(ledger) ? ledger : []) {
    if (!rec || typeof rec !== 'object' || Array.isArray(rec)) continue;
    if (rec.op === 'unit-seed') {
      for (const u of Array.isArray(rec.units) ? rec.units : []) push(u && u.id, u && u.path, rec.pass, 'unit-seed');
    } else if (rec.op === 'unit-add' && rec.unit) {
      push(rec.unit.id, rec.unit.path, rec.pass, 'unit-add');
    } else if (rec.op === 'unit-edit' && rec.set && Object.prototype.hasOwnProperty.call(rec.set, 'path')) {
      push(rec.target, rec.set.path, rec.pass, 'unit-edit');
    }
  }
  return map;
}

/** How a path came to be on a unit, for the refusal message. */
const pathSourcePhrase = (entry) =>
  entry.source === 'unit-edit'
    ? `set by a unit-edit in pass ${entry.pass}`
    : entry.source === 'unit-add'
      ? `carried by the unit-add that created it in pass ${entry.pass}`
      : entry.source === 'unit-seed'
        ? `enumerated with it in pass ${entry.pass}`
        : 'the value currently in units.json';

function normaliseUnit(raw, { pass, errs, where, unitIds, lensUnit }) {
  if (raw === null || typeof raw !== 'object' || Array.isArray(raw)) {
    errs.push(`${where}: "unit" must be an object.`);
    return null;
  }
  const id = raw.id;
  if (typeof id !== 'string' || id.trim() === '') {
    errs.push(`${where}: unit is missing a string "id".`);
  } else if (!UNIT_ID_RE.test(id)) {
    errs.push(`${where}: unit id "${id}" must be a lowercase dotted slug (a-z, 0-9, ".", "-", "_").`);
  } else if (unitIds.has(id)) {
    errs.push(`${where}: unit id "${id}" already exists.`);
  }
  if (typeof raw.label !== 'string' || raw.label.trim() === '') {
    errs.push(`${where}: unit "${id}" is missing a string "label".`);
  }
  if (raw.path !== undefined && raw.path !== null && typeof raw.path !== 'string') {
    errs.push(`${where}: unit "${id}" has a non-string "path".`);
  }
  if (raw.meta !== undefined && raw.meta !== null && (typeof raw.meta !== 'object' || Array.isArray(raw.meta))) {
    errs.push(`${where}: unit "${id}" has a non-object "meta".`);
  }
  return {
    id,
    label: raw.label,
    path: raw.path ?? null,
    kind: raw.kind ?? lensUnit ?? null,
    meta: raw.meta ?? {},
    addedInPass: pass,
  };
}

/** Normalise + validate a whole inventory (the `ponder units` payload). */
export function normaliseUnits(rawUnits, { pass = 1, lensUnit = null } = {}) {
  const errs = [];
  const seen = new Set();
  const units = [];
  if (!Array.isArray(rawUnits)) throw userError('units payload must be an array, or an object with a "units" array.');
  rawUnits.forEach((raw, i) => {
    const unit = normaliseUnit(raw, { pass, errs, where: `unit ${i + 1}`, unitIds: seen, lensUnit });
    if (unit && unit.id) seen.add(unit.id);
    if (unit) units.push(unit);
  });
  if (errs.length) throw userError(`the unit inventory has ${errs.length} problem${errs.length === 1 ? '' : 's'}.`, errs);
  if (units.length === 0) throw userError('the unit inventory is empty — coverage over zero units is not a pondering.');
  return units;
}

// ---------------------------------------------------------------------------
// application
// ---------------------------------------------------------------------------

const isLiveUnit = (u) => !u.removedInPass;

/**
 * The removal kind of a unit that has left the inventory, `null` while it is still in.
 *
 * Sessions written before removal kinds existed carry only `removedInPass`. Their kind is
 * inferred the same way the engine would decide it today — a unit that was appraised is an
 * `appraised` removal, one that never was is `removed-ungraded` — so an old session cannot
 * inherit a coverage escape that the current rules close.
 *
 * `appraised` is re-derived rather than believed. SPEC 3.5 *defines* an appraised removal as
 * one whose unit carries at least one finding, and both of the kinds that shrink the coverage
 * denominator are read straight off `units.json`. A stored `appraised` on a unit with no
 * findings therefore contradicts its own definition — whether it got there by a hand-edit or
 * by a future bug — and the definition wins, so the unit stays in the denominator.
 */
export function removalKindOf(unit, appraisedUnitIds) {
  if (!unit || !unit.removedInPass) return null;
  const appraised = Boolean(appraisedUnitIds && appraisedUnitIds.has(unit.id));
  if (REMOVAL_KINDS.includes(unit.removalKind)) {
    if (unit.removalKind === 'appraised' && !appraised) return 'removed-ungraded';
    return unit.removalKind;
  }
  return appraised ? 'appraised' : 'removed-ungraded';
}

/**
 * Validate and apply a batch of deltas.
 *
 * Returns { findings, units, records, summary }. `records` are the ledger lines to append,
 * with the engine-assigned ids filled in. Throws a userError listing every problem when
 * anything is wrong — nothing is written in that case.
 *
 * `projectRoot` is where a phantom claim's `path` is resolved from. Without it a phantom
 * claim on a unit that has a path cannot be checked, so the batch is refused rather than
 * quietly recorded as unverified.
 *
 * `unitPaths` is `unitPathHistory(ledger)` — every path each unit has ever carried. A
 * phantom claim is checked against all of them, not just the one in units.json today,
 * because `unit-edit` can move a path (SPEC 3.5).
 *
 * `projectRootGuessed` says the root above was found rather than established — no project
 * marker decided it (SPEC 3.1). A path that does not resolve under a guessed root is not
 * evidence that a screen is absent; it is evidence that the engine may be looking in the
 * wrong place. A phantom claim in that state is refused rather than certified or quietly
 * recorded unverified (SPEC 3.5). `projectRootOrigin` is the phrase used to say why.
 */
export function applyDeltas(entries, { findings, units, pass, source = 'delta', now = new Date().toISOString(), projectRoot = null, projectRootGuessed = false, projectRootOrigin = null, unitPaths = new Map() }) {
  const errs = [];
  const nextFindings = structuredClone(findings);
  const nextUnits = structuredClone(units);
  const findingById = new Map(nextFindings.map((f) => [f.id, f]));
  const unitById = new Map(nextUnits.map((u) => [u.id, u]));
  const records = [];
  let idCursor = 0;
  const seedId = nextFindingId(nextFindings);

  // A working copy of the path history, so a path set earlier in *this* batch is checked
  // by a phantom claim later in the same batch. Otherwise the attack is one file away:
  // unit-edit the path and unit-delete --phantom it on the next line.
  const paths = new Map();
  for (const [id, list] of unitPaths) paths.set(id, [...list]);
  const notePath = (id, value, src) => {
    if (!paths.has(id)) paths.set(id, []);
    paths.get(id).push({
      path: typeof value === 'string' && value.trim() !== '' ? value.trim() : null,
      pass,
      source: src,
    });
  };

  for (const { delta, line } of entries) {
    const where = `delta line ${line}`;
    if (delta === null || typeof delta !== 'object' || Array.isArray(delta)) {
      errs.push(`${where}: each delta must be a JSON object.`);
      continue;
    }
    const op = delta.op;
    if (!OPS.includes(op)) {
      errs.push(`${where}: op must be one of ${OPS.join(', ')} (got ${JSON.stringify(op)}).`);
      continue;
    }
    const why = typeof delta.why === 'string' ? delta.why.trim() : '';
    if (why === '') {
      errs.push(`${where}: every delta needs a non-empty "why" — an unexplained revision is not a revision.`);
    }
    if (delta.phantom !== undefined && op !== 'unit-delete') {
      errs.push(`${where}: "phantom" belongs to unit-delete only — it claims a unit does not exist in the software.`);
    }
    if (delta.pass !== undefined && delta.pass !== null && Number(delta.pass) !== Number(pass)) {
      errs.push(`${where}: delta says pass ${delta.pass} but this session is on pass ${pass}.`);
    }
    const perspective = delta.perspective ?? null;
    if (source === 'delta') {
      if (perspective === null) {
        errs.push(`${where}: every delta needs a "perspective" (${PERSPECTIVES.join(', ')}).`);
      } else if (!PERSPECTIVES.includes(perspective)) {
        errs.push(`${where}: perspective "${perspective}" is not one of ${PERSPECTIVES.join(', ')}.`);
      }
    }

    const record = {
      pass,
      op,
      perspective,
      why,
      at: typeof delta.at === 'string' ? delta.at : now,
    };
    if (source !== 'delta') record.source = source;

    if (op === 'add') {
      const id = seedId(++idCursor);
      const finding = normaliseFinding(delta.finding, { pass, id, errs, where });
      if (finding) {
        nextFindings.push(finding);
        findingById.set(id, finding);
        const unit = unitById.get(finding.unit);
        if (!unit) {
          errs.push(`${where}: finding targets unknown unit "${finding.unit}" — add it first with a unit-add delta.`);
        } else if (!isLiveUnit(unit)) {
          errs.push(`${where}: unit "${finding.unit}" was removed in pass ${unit.removedInPass}.`);
        }
        const { id: _drop, createdInPass, lastTouchedPass, history, ...body } = finding;
        record.id = id;
        record.target = id;
        record.finding = body;
        records.push(record);
      }
      continue;
    }

    if (op === 'unit-add') {
      const unit = normaliseUnit(delta.unit, {
        pass,
        errs,
        where,
        unitIds: new Set(nextUnits.map((u) => u.id)),
        lensUnit: null,
      });
      if (unit && unit.id) {
        nextUnits.push(unit);
        unitById.set(unit.id, unit);
        notePath(unit.id, unit.path, 'unit-add');
        record.target = unit.id;
        record.unit = unit;
        records.push(record);
      }
      continue;
    }

    const target = delta.target;
    if (typeof target !== 'string' || target.trim() === '') {
      errs.push(`${where}: op "${op}" needs a "target".`);
      continue;
    }
    record.target = target;

    if (op === 'unit-edit') {
      const unit = unitById.get(target);
      if (!unit) {
        errs.push(`${where}: unknown unit "${target}".`);
        continue;
      }
      if (!isLiveUnit(unit)) {
        errs.push(
          `${where}: unit "${target}" was removed in pass ${unit.removedInPass} — a unit that has left the inventory is not edited back into shape, it is re-added.`,
        );
        continue;
      }
      const set = delta.set;
      if (set === null || typeof set !== 'object' || Array.isArray(set) || Object.keys(set).length === 0) {
        errs.push(`${where}: op "unit-edit" needs a non-empty "set" object.`);
        continue;
      }
      if (Object.prototype.hasOwnProperty.call(set, 'id')) {
        errs.push(
          `${where}: unit-edit may never set "id". The unit id is the join key between units.json and findings.json, so changing it would orphan every finding on "${target}". If the id itself is wrong, delete the unit and add the corrected one, and accept what that costs coverage.`,
        );
        continue;
      }
      const applied = {};
      let fieldErrors = 0;
      for (const [field, value] of Object.entries(set)) {
        const before = errs.length;
        checkUnitField(field, value, errs, where, target);
        if (errs.length > before) {
          fieldErrors++;
          continue;
        }
        applied[field] = value;
      }
      if (fieldErrors > 0) continue;
      for (const [field, value] of Object.entries(applied)) {
        if (field === 'meta') {
          // meta merges key by key (SPEC 3.4): correcting a unit's route must not wipe the
          // state marker sitting beside it in the same object.
          unit.meta = { ...(unit.meta && typeof unit.meta === 'object' ? unit.meta : {}), ...value };
          continue;
        }
        unit[field] = value;
        if (field === 'path') notePath(target, value, 'unit-edit');
      }
      record.set = applied;
      records.push(record);
      continue;
    }

    if (op === 'unit-delete') {
      const unit = unitById.get(target);
      if (!unit) {
        errs.push(`${where}: unknown unit "${target}".`);
        continue;
      }

      const phantom = delta.phantom;
      if (phantom !== undefined && typeof phantom !== 'boolean') {
        errs.push(`${where}: "phantom" must be true or false (got ${JSON.stringify(phantom)}).`);
        continue;
      }
      // "Appraised" means the unit was genuinely looked at once: a retracted finding still
      // counts, because withdrawing a judgment does not un-see the thing it judged.
      const appraised = nextFindings.some((f) => f.unit === target);
      const priorKind = removalKindOf(unit, new Set(appraised ? [target] : []));

      if (priorKind !== null) {
        // The one legal re-delete: upgrading a removed-ungraded unit to a checked phantom
        // claim. Anything else is a repeat of a delete that already happened.
        if (!(priorKind === 'removed-ungraded' && phantom === true)) {
          errs.push(`${where}: unit "${target}" was already removed in pass ${unit.removedInPass}.`);
          continue;
        }
      }

      if (phantom === true && appraised) {
        errs.push(
          `${where}: unit "${target}" carries ${plural(nextFindings.filter((f) => f.unit === target).length, 'finding')}, so it was appraised — it cannot also be a unit that never existed. Delete it without "phantom" and say in the why what changed the scope.`,
        );
        continue;
      }

      if (appraised) {
        unit.removedInPass = pass;
        unit.removalKind = 'appraised';
        record.removal = 'appraised';
        records.push(record);
        continue;
      }

      if (phantom !== true) {
        // Never graded and no phantom claim: the unit leaves the inventory but stays in the
        // coverage denominator. This is the whole point — deleting what you never looked at
        // must not be the cheap way past the gate.
        unit.removedInPass = pass;
        unit.removalKind = 'removed-ungraded';
        record.removal = 'removed-ungraded';
        records.push(record);
        continue;
      }

      // A phantom claim is checked, not trusted — and it is checked against EVERY path the
      // unit has ever carried, not just the one units.json holds now (SPEC 3.5).
      //
      // `unit-edit` can move a path. Checking only the current value would hand an agent
      // that wants to stop early a two-delta route through the coverage gate: point a real
      // unit at a filename that does not exist, then claim the unit never existed and let
      // the engine certify it. So the original path from `unit-seed` / `unit-add` and every
      // value any `unit-edit` has set are all candidates, and one survivor sinks the claim.
      const history = paths.get(target) || [];
      const candidates = [...history];
      const current = typeof unit.path === 'string' && unit.path.trim() !== '' ? unit.path.trim() : null;
      if (current && !candidates.some((c) => c.path === current)) {
        candidates.push({ path: current, pass: unit.addedInPass ?? null, source: 'units.json' });
      }
      const named = candidates.filter((c) => c.path !== null);
      const moved = history.some((c) => c.source === 'unit-edit');

      if (named.length && !projectRoot) {
        errs.push(
          `${where}: unit "${target}" is claimed phantom and has ${plural(named.length, 'path')} to check (${[...new Set(named.map((c) => c.path))].join(', ')}), but there is no project root to resolve them against, so the claim cannot be checked.`,
        );
        continue;
      }

      let found = null;
      const checked = [];
      for (const candidate of named) {
        const abs = path.isAbsolute(candidate.path) ? candidate.path : path.resolve(projectRoot, candidate.path);
        checked.push(abs);
        if (fs.existsSync(abs)) {
          found = { ...candidate, abs };
          break;
        }
      }
      if (found) {
        errs.push(
          `${where}: unit "${target}" is claimed phantom, but a path it has carried exists: ${found.abs} (${pathSourcePhrase(found)}). Something you can open is not something pass 1 imagined.${
            moved ? ' A phantom claim is checked against every path the unit has ever had, so editing the path first does not clear it.' : ''
          }`,
        );
        continue;
      }

      // Every named path missed — but under a root nothing established, a miss says as much
      // about the root as about the screen (SPEC 3.1, 3.5). Refuse the claim and name the
      // root, rather than record an absence that was never really checked.
      if (named.length && projectRootGuessed) {
        errs.push(
          `${where}: unit "${target}" is claimed phantom and none of the ${plural(named.length, 'path')} it has carried (${[
            ...new Set(named.map((c) => c.path)),
          ].join(', ')}) resolves under ${projectRoot} — but that project root was guessed, not established${
            projectRootOrigin ? ` (${projectRootOrigin})` : ''
          }. A file that is missing from the wrong directory is not a screen that never existed. Point the session at the real project root and claim it again:  ponder start … --project <path>`,
        );
        continue;
      }

      unit.removedInPass = pass;
      unit.removalKind = 'phantom';
      record.removal = 'phantom';
      record.phantom = true;

      if (named.length && !moved) {
        // One path, never moved, and it is not there: the engine can certify the absence.
        const abs = checked[0];
        unit.phantomVerification = 'verified-missing';
        unit.phantomPath = abs;
        record.verification = 'verified-missing';
        record.verifiedPath = abs;
        records.push(record);
        continue;
      }

      // Either the unit never had a path, or its path was edited. A moved target is one the
      // engine cannot certify an absence about: every version of the path is missing, but
      // "missing" and "never existed" are only the same claim when the target never moved.
      // The phantom is accepted and permanently marked unverified (SPEC 3.5).
      unit.phantomVerification = 'unverified';
      unit.phantomPath = null;
      record.verification = 'unverified';
      if (moved) record.pathsChecked = [...new Set(checked)];
      records.push(record);
      continue;
    }

    const finding = findingById.get(target);
    if (!finding) {
      errs.push(`${where}: unknown finding "${target}".`);
      continue;
    }

    if (op === 'delete') {
      if (finding.status === 'retracted') {
        errs.push(`${where}: ${target} is already retracted (pass ${finding.lastTouchedPass}).`);
        continue;
      }
      finding.history.push({ pass, op: 'delete', field: 'status', from: finding.status, to: 'retracted' });
      finding.status = 'retracted';
      finding.lastTouchedPass = pass;
      records.push(record);
      continue;
    }

    // edit | change
    const set = delta.set;
    if (set === null || typeof set !== 'object' || Array.isArray(set) || Object.keys(set).length === 0) {
      errs.push(`${where}: op "${op}" needs a non-empty "set" object.`);
      continue;
    }
    const applied = {};
    let fieldErrors = 0;
    for (const [field, value] of Object.entries(set)) {
      const before = errs.length;
      checkField(field, value, errs, where);
      if (errs.length > before) {
        fieldErrors++;
        continue;
      }
      if (field === 'unit') {
        const unit = unitById.get(value);
        if (!unit || !isLiveUnit(unit)) {
          errs.push(`${where}: cannot move ${target} to unknown or removed unit "${value}".`);
          fieldErrors++;
          continue;
        }
      }
      applied[field] = value;
    }
    if (fieldErrors > 0) continue;
    for (const [field, value] of Object.entries(applied)) {
      const from = finding[field];
      if (JSON.stringify(from) === JSON.stringify(value)) continue;
      finding.history.push({ pass, op, field, from: from === undefined ? null : from, to: value });
      finding[field] = value;
    }
    finding.lastTouchedPass = pass;
    record.set = applied;
    records.push(record);
  }

  if (errs.length) {
    throw userError(
      `${errs.length} problem${errs.length === 1 ? '' : 's'} in this delta batch — nothing was applied.`,
      errs,
    );
  }

  return {
    findings: nextFindings,
    units: nextUnits,
    records,
    summary: summariseDeltas(records),
  };
}

/** Turn the seeded pass-1 finding set into `add` deltas so the ledger holds every creation. */
export function seedEntries(rawFindings, { why = 'Pass 1 appraisal against the lens rubric.' } = {}) {
  if (!Array.isArray(rawFindings)) {
    throw userError('findings payload must be an array, or an object with a "findings" array.');
  }
  return rawFindings.map((finding, i) => ({
    delta: { op: 'add', perspective: null, why: finding && finding.why ? String(finding.why) : why, finding: stripSeedMeta(finding) },
    line: i + 1,
  }));
}

function stripSeedMeta(finding) {
  if (!finding || typeof finding !== 'object' || Array.isArray(finding)) return finding;
  const { why, id, createdInPass, lastTouchedPass, history, ...rest } = finding;
  return rest;
}

/**
 * Summarise ledger records.
 *
 * Only the six delta ops are counted. The ledger also carries the `unit-seed` record that
 * puts the pass-1 inventory on the record (SPEC 3.4); it is a seed, not a revision, so
 * counting it would make "17 deltas: 12 add, 4 edit" fail to add up.
 */
export function summariseDeltas(records) {
  const byOp = Object.fromEntries(OPS.map((op) => [op, 0]));
  const voices = new Set();
  let total = 0;
  for (const r of records) {
    if (!r || !OPS.includes(r.op)) continue;
    total++;
    byOp[r.op] = (byOp[r.op] || 0) + 1;
    if (PERSPECTIVES.includes(r.perspective)) voices.add(r.perspective);
  }
  return { total, byOp, voices: [...voices].sort() };
}

/** "4 add, 2 edit, 1 delete" — the phrase used in reports and OCA resolutions. */
export function describeDeltas(summary) {
  if (!summary || summary.total === 0) return 'no deltas';
  return OPS.filter((op) => summary.byOp[op] > 0)
    .map((op) => `${summary.byOp[op]} ${op}`)
    .join(', ');
}

/** Findings that count as a grade for coverage: anything not withdrawn. */
export function isGradingFinding(f) {
  return f.status !== 'retracted';
}
