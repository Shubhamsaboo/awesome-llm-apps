// The eight convergence signals (SPEC 4), computed from the ledger at `ponder judge`.
//
// Everything here is a pure function of on-disk state: the unit inventory, the finding set,
// the append-only ledger and this pass's prediction. Nothing is remembered between runs
// except what those files say, which is what makes a session resumable from nothing.

import { OPS, PERSPECTIVES, SEVERITY_RANK, removalKindOf } from './deltas.js';

const STALL_CHURN = 0.02;

const r4 = (n) => (n === null || n === undefined || Number.isNaN(n) ? null : Math.round(n * 10000) / 10000);
const eq = (a, b) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
const ratio = (num, den) => (den === 0 ? 0 : num / den);

/** Fields whose creation value we track, so a revert to the original counts as a reversal. */
const TRACKED_FIELDS = [
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

/** Unit fields a `unit-edit` can move, tracked so a label edited back and forth thrashes. */
const TRACKED_UNIT_FIELDS = ['label', 'path', 'kind', 'meta'];

/**
 * Find every delta in `pass` that reverses an earlier one (SPEC 4).
 *
 * Three cases, all implemented:
 *  1. field-revert   — an earlier pass set F to X, a later pass set F to something else,
 *                      this pass sets F back to X. A finding's creation values count as
 *                      the first setting, and so do a unit's: `unit-edit` is a revising
 *                      delta, so a label corrected in pass 2 and put back in pass 3 is
 *                      oscillation exactly like a severity flipped back and forth.
 *  2. revived-delete — this pass `add`s a finding materially matching one an earlier pass
 *                      `delete`d: same unit AND same dimension (both must be present).
 *  3. killed-add     — this pass `delete`s a finding an earlier pass `add`ed within the
 *                      previous two passes. Pass-1 seeding is not a deliberative add, so
 *                      grade-sourced adds are excluded: killing pass 1's noise in pass 2
 *                      is the Skeptic working, not the loop oscillating.
 *
 * Returns one record per reversing delta, so `thrash` counts deltas, not fields.
 */
export function findReversals(ledger, pass, findings) {
  const findingById = new Map(findings.map((f) => [f.id, f]));
  const fieldHistory = new Map(); // `${target}\u0000${field}` -> [{pass, value}]
  const addPassById = new Map(); // id -> pass, deliberative adds only
  const deletedSignatures = []; // {unit, dimension, pass, id}

  const pushField = (target, field, p, value) => {
    const key = `${target}\u0000${field}`;
    if (!fieldHistory.has(key)) fieldHistory.set(key, []);
    fieldHistory.get(key).push({ pass: p, value });
  };

  // Units are tracked by their *effective* value, not by the raw `set`, because `meta`
  // merges key by key (SPEC 3.4): two edits that touch different meta keys are not a
  // reversal just because one of them repeats an earlier partial object.
  const unitState = new Map();
  const seedUnit = (u, p) => {
    if (!u || typeof u.id !== 'string') return;
    const state = { label: u.label, path: u.path ?? null, kind: u.kind ?? null, meta: u.meta ?? {} };
    unitState.set(u.id, state);
    for (const field of TRACKED_UNIT_FIELDS) pushField(u.id, field, p, state[field]);
  };
  /** Apply a unit-edit's set to the tracked state; returns the effective values it wrote. */
  const applyUnitEdit = (id, set) => {
    const state = unitState.get(id);
    if (!state || !set || typeof set !== 'object') return null;
    const effective = {};
    for (const [field, value] of Object.entries(set)) {
      if (!TRACKED_UNIT_FIELDS.includes(field)) continue;
      if (field === 'meta') {
        const base = state.meta && typeof state.meta === 'object' ? state.meta : {};
        state.meta = { ...base, ...(value && typeof value === 'object' ? value : {}) };
        effective.meta = state.meta;
        continue;
      }
      state[field] = value;
      effective[field] = value;
    }
    return effective;
  };

  for (const rec of ledger) {
    if (!rec || typeof rec !== 'object') continue;
    if (Number(rec.pass) >= Number(pass)) continue; // history is strictly earlier passes
    const target = rec.target ?? rec.id ?? null;
    if (rec.op === 'unit-seed') {
      for (const u of Array.isArray(rec.units) ? rec.units : []) seedUnit(u, Number(rec.pass));
      continue;
    }
    if (rec.op === 'unit-add') {
      seedUnit(rec.unit, Number(rec.pass));
      continue;
    }
    if (rec.op === 'unit-edit' && target) {
      const effective = applyUnitEdit(target, rec.set);
      if (effective) {
        for (const [field, value] of Object.entries(effective)) pushField(target, field, Number(rec.pass), value);
      }
      continue;
    }
    if (rec.op === 'add' && target) {
      if (rec.source !== 'grade') addPassById.set(target, Number(rec.pass));
      const body = rec.finding || {};
      for (const field of TRACKED_FIELDS) {
        if (body[field] !== undefined) pushField(target, field, Number(rec.pass), body[field]);
      }
    } else if ((rec.op === 'edit' || rec.op === 'change') && target && rec.set) {
      for (const [field, value] of Object.entries(rec.set)) pushField(target, field, Number(rec.pass), value);
    } else if (rec.op === 'delete' && target) {
      pushField(target, 'status', Number(rec.pass), 'retracted');
      const f = findingById.get(target);
      if (f && f.unit && f.dimension) {
        deletedSignatures.push({ unit: f.unit, dimension: f.dimension, pass: Number(rec.pass), id: target });
      }
    }
  }

  const reversals = [];
  for (const rec of ledger) {
    if (!rec || Number(rec.pass) !== Number(pass)) continue;
    const target = rec.target ?? rec.id ?? null;

    if (rec.op === 'add') {
      const body = rec.finding || {};
      if (body.unit && body.dimension) {
        const hit = deletedSignatures.find((d) => d.unit === body.unit && d.dimension === body.dimension);
        if (hit) {
          reversals.push({
            kind: 'revived-delete',
            op: rec.op,
            target,
            against: hit.id,
            note: `re-adds ${body.unit} / ${body.dimension}, which pass ${hit.pass} deleted as ${hit.id}`,
          });
        }
      }
      continue;
    }

    if (rec.op === 'delete' && target) {
      const addedIn = addPassById.get(target);
      if (addedIn !== undefined && addedIn < pass && pass - addedIn <= 2) {
        reversals.push({
          kind: 'killed-add',
          op: rec.op,
          target,
          against: target,
          note: `deletes ${target}, added in pass ${addedIn}`,
        });
      }
      continue;
    }

    if (rec.op === 'unit-edit' && target && rec.set) {
      // A unit-edit is a revising delta like any other, so a label put back to what an
      // earlier pass already said is oscillation and counts toward thrash (SPEC 4).
      const effective = applyUnitEdit(target, rec.set);
      const reverted = [];
      for (const [field, value] of Object.entries(effective || {})) {
        const hist = fieldHistory.get(`${target}\u0000${field}`) || [];
        if (hist.length < 2) continue;
        const last = hist[hist.length - 1];
        pushField(target, field, Number(rec.pass), value);
        if (eq(last.value, value)) continue;
        const earlier = hist.slice(0, -1).find((h) => eq(h.value, value));
        if (earlier) reverted.push({ field, wasSetInPass: earlier.pass, overwrittenInPass: last.pass });
      }
      if (reverted.length) {
        reversals.push({
          kind: 'field-revert',
          op: rec.op,
          target,
          against: target,
          fields: reverted.map((r) => r.field),
          note: reverted
            .map((r) => `${target}.${r.field} back to the pass ${r.wasSetInPass} value after pass ${r.overwrittenInPass} changed it`)
            .join('; '),
        });
      }
      continue;
    }

    if ((rec.op === 'edit' || rec.op === 'change') && target && rec.set) {
      const reverted = [];
      for (const [field, value] of Object.entries(rec.set)) {
        const hist = fieldHistory.get(`${target}\u0000${field}`) || [];
        if (hist.length < 2) continue;
        const last = hist[hist.length - 1];
        if (eq(last.value, value)) continue; // not a change away from the current value
        // Any earlier setting counts, not only one from an earlier pass: seeding a finding
        // and re-grading it inside pass 1, then putting the grade back in pass 2, is the
        // commonest oscillation there is, and a pass-number comparison misses all of it.
        const earlier = hist.slice(0, -1).find((h) => eq(h.value, value));
        if (earlier) {
          reverted.push({ field, value, wasSetInPass: earlier.pass, overwrittenInPass: last.pass });
        }
      }
      if (reverted.length) {
        reversals.push({
          kind: 'field-revert',
          op: rec.op,
          target,
          against: target,
          fields: reverted.map((r) => r.field),
          note: reverted
            .map((r) =>
              r.wasSetInPass === r.overwrittenInPass
                ? `${target}.${r.field} back to the value pass ${r.wasSetInPass} both set and then changed`
                : `${target}.${r.field} back to the pass ${r.wasSetInPass} value after pass ${r.overwrittenInPass} changed it`,
            )
            .join('; '),
        });
      }
    }
  }
  return reversals;
}

/**
 * Which units carry at least one standing grade, and which do not (SPEC 4).
 *
 * The denominator is every unit still in scope. A unit leaves the denominator two ways
 * only: it was appraised and then dropped (an honest scope change), or it was claimed —
 * and where possible verified — as a phantom that never existed in the software. A unit
 * deleted without ever being graded stays in the denominator under `removed-ungraded`,
 * which is what closes the delete-what-you-never-looked-at escape.
 */
export function coverageOf(units, findings) {
  const appraised = new Set(findings.map((f) => f.unit)); // retracted judgments included
  const graded = new Set();
  for (const f of findings) {
    if (f.status === 'retracted') continue; // a withdrawn judgment is not a grade
    graded.add(f.unit);
  }

  const counted = [];
  const removedUngraded = [];
  const removedAppraised = [];
  const phantoms = [];
  for (const u of units) {
    const kind = removalKindOf(u, appraised);
    if (kind === null) counted.push(u);
    else if (kind === 'removed-ungraded') {
      counted.push(u);
      removedUngraded.push(u);
    } else if (kind === 'phantom') phantoms.push(u);
    else removedAppraised.push(u);
  }

  const gradedUnits = counted.filter((u) => graded.has(u.id));
  const ungraded = counted.filter((u) => !graded.has(u.id));
  return {
    enumerated: counted.length,
    graded: gradedUnits.length,
    ungraded: ungraded.map((u) => u.id),
    ungradedUnits: ungraded,
    // Still counted against coverage even though they are out of the inventory.
    removedUngraded: removedUngraded.map((u) => u.id),
    removedUngradedUnits: removedUngraded,
    removedAppraised: removedAppraised.map((u) => u.id),
    phantoms: phantoms.map((u) => ({ id: u.id, verification: u.phantomVerification || 'unverified', pass: u.removedInPass })),
    phantomUnits: phantoms,
    // Every unit that has left the inventory, whatever it cost coverage.
    removed: units.filter((u) => u.removedInPass).map((u) => u.id),
    coverage: counted.length === 0 ? 0 : gradedUnits.length / counted.length,
  };
}

export function countFindings(findings) {
  const counts = { total: findings.length, open: 0, resolved: 0, retracted: 0, deferred: 0 };
  for (const f of findings) counts[f.status] = (counts[f.status] || 0) + 1;
  counts.live = counts.total - counts.retracted;
  return counts;
}

/**
 * Compute every signal for `pass`.
 * `priorMetrics` is the ordered list of previous passes' metrics.json (may contain holes).
 */
export function computeMetrics({ session, units, findings, ledger, pass, predict, priorMetrics = [], deliberation = null }) {
  const cov = coverageOf(units, findings);
  const counts = countFindings(findings);
  // The ledger holds more than deltas: `unit-seed` records the pass-1 inventory so that no
  // unit can enter the session without a line (SPEC 3.4). It is not a revision of anything,
  // so it is not in any ratio, any count, or `deltas.total`.
  const passDeltas = ledger.filter((r) => r && OPS.includes(r.op) && Number(r.pass) === Number(pass));
  const byOp = {};
  for (const r of passDeltas) byOp[r.op] = (byOp[r.op] || 0) + 1;
  // Pass 1's `ponder grade` seeding is recorded as add deltas so that every finding has a
  // creation record in the ledger (the thrash detector reads creation values as the first
  // setting of a field). Those deltas are the baseline, not a revision of one, so they are
  // excluded from the numerator of every ratio below and reported separately as `seeded`.
  const seeded = passDeltas.filter((r) => r.source === 'grade').length;
  const revisions = passDeltas.filter((r) => r.source !== 'grade');

  const totalFindings = counts.live; // the live set — retracted findings must not dilute novelty
  const totalDeltas = passDeltas.length;
  const revisionCount = revisions.length;
  const adds = revisions.filter((r) => r.op === 'add').length;

  const reversals = findReversals(ledger, pass, findings);

  // SPEC 4: novelty, churn and thrash are change measured against a previous pass. Pass 1
  // has no previous pass, so it has none of them — and neither does surprise, which is
  // scored against churn. They are emitted as null and rendered as "—". A pass-1 1.00 /
  // 1.13 / 0.00 was three numbers describing nothing.
  const firstPass = Number(pass) <= 1;
  const novelty = firstPass ? null : ratio(adds, totalFindings);
  const churn = firstPass ? null : ratio(revisionCount, totalFindings);
  const thrash = firstPass ? null : ratio(reversals.length, revisionCount);

  const predictedChurn = predict && typeof predict.churn === 'number' ? predict.churn : null;
  const surprise = predictedChurn === null || churn === null ? null : Math.abs(predictedChurn - churn);

  let stall = 0;
  if (typeof churn === 'number' && churn < STALL_CHURN) {
    stall = 1;
    for (let p = pass - 1; p >= 1; p--) {
      const m = priorMetrics.find((x) => x && Number(x.pass) === p);
      if (m && typeof m.churn === 'number' && m.churn < STALL_CHURN) stall++;
      else break;
    }
  }

  const importantOpen = findings.filter((f) => f.status === 'open' && f.severity === 'must');
  const shaky = importantOpen.filter((f) => Number(f.confidence) < 0.5);
  const confidenceFloor = ratio(shaky.length, importantOpen.length);

  // SPEC 4: `voices` counts who spoke in the pass's deliberation, not who emitted a delta.
  // A perspective that argues "nothing to change here" has spoken. Delta attribution is
  // kept alongside it, because that is what the ledger and the thrash detector read.
  const spoke =
    deliberation && !deliberation.skipped && deliberation.perspectives
      ? Object.keys(deliberation.perspectives).filter((p) => PERSPECTIVES.includes(p)).sort()
      : [];
  const deltaVoices = [...new Set(revisions.map((d) => d.perspective).filter((p) => PERSPECTIVES.includes(p)))].sort();

  return {
    version: 1,
    pass: Number(pass),
    at: new Date().toISOString(),
    coverage: r4(cov.coverage),
    novelty: r4(novelty),
    churn: r4(churn),
    thrash: r4(thrash),
    surprise: r4(surprise),
    stall,
    confidenceFloor: r4(confidenceFloor),
    voices: spoke.length,
    voiceNames: spoke,
    deliberationSkipped: Boolean(deliberation && deliberation.skipped),
    deltaVoices: deltaVoices.length,
    deltaVoiceNames: deltaVoices,
    predictedChurn: r4(predictedChurn),
    claim: predict && typeof predict.claim === 'string' ? predict.claim : null,
    units: {
      enumerated: cov.enumerated,
      graded: cov.graded,
      removed: cov.removed.length,
      removedUngraded: cov.removedUngraded.length,
      phantom: cov.phantoms.length,
    },
    ungraded: cov.ungraded,
    removedUngraded: cov.removedUngraded,
    phantoms: cov.phantoms,
    findings: counts,
    deltas: { total: totalDeltas, byOp, seeded, revisions: revisionCount },
    reversals,
    shakyMustFindings: shaky.map((f) => f.id),
    minPasses: session.minPasses,
    maxPasses: session.maxPasses,
  };
}

/** Load every earlier pass's metrics so stall and the 2-pass convergence rule can be read. */
export function priorMetricsFor(loadPassArtifact, dir, pass) {
  const out = [];
  for (let p = 1; p < pass; p++) {
    const m = loadPassArtifact(dir, p, 'metrics.json');
    if (m) out.push(m);
  }
  return out;
}

/**
 * Metacognitive observations this pass earns (SPEC 6.1). `deliberation_skipped` is not here
 * — it is recorded the moment the agent skips, not at judge.
 */
export function metacognitionTriggers(metrics) {
  const out = [];
  // Every threshold below is guarded on the signal actually being a number: pass 1 emits
  // null for novelty, churn, thrash and surprise, and a null must never read as a zero
  // that clears a bar or as a value that trips one.
  if (typeof metrics.thrash === 'number' && metrics.thrash > 0.25) {
    out.push({
      type: 'thrash',
      description: `Pass ${metrics.pass} reversed ${metrics.reversals.length} of ${metrics.deltas.revisions ?? metrics.deltas.total} revising deltas (thrash ${metrics.thrash}).`,
      evidence: metrics.reversals.slice(0, 8).map((r) => `${r.kind}: ${r.note}`),
      severity: 'high',
      intervention: 'Rotate perspectives, widen the evidence, or split the subject. Another identical pass will oscillate again.',
    });
  }
  if (metrics.stall >= 2 && metrics.coverage >= 1) {
    out.push({
      type: 'perseveration',
      description: `${metrics.stall} consecutive passes below ${STALL_CHURN} churn with full coverage.`,
      evidence: [`churn ${metrics.churn}`, `novelty ${metrics.novelty}`],
      severity: 'medium',
      intervention: 'Stop. Further passes are theatre.',
    });
  }
  if (metrics.stall >= 2 && metrics.coverage < 1) {
    out.push({
      type: 'stuck_state',
      description: `${metrics.stall} consecutive passes below ${STALL_CHURN} churn while coverage is ${metrics.coverage}.`,
      evidence: metrics.ungraded.slice(0, 12),
      severity: 'high',
      intervention: 'Nothing is moving and units are still ungraded. Grade the ungraded units directly instead of re-reading the graded ones.',
    });
  }
  if (metrics.confidenceFloor > 0.2) {
    out.push({
      type: 'low_confidence',
      description: `${Math.round(metrics.confidenceFloor * 100)}% of open must-severity findings sit below 0.5 confidence.`,
      evidence: metrics.shakyMustFindings.slice(0, 12),
      severity: 'medium',
      intervention: 'Gather evidence for those findings or downgrade their severity. A must you cannot defend is not a must.',
    });
  }
  return out;
}

/** Sort key used by report and apply-plan: worst first. */
export function findingOrder(a, b) {
  const sev = (SEVERITY_RANK[a.severity] ?? 9) - (SEVERITY_RANK[b.severity] ?? 9);
  if (sev !== 0) return sev;
  const score = (a.score ?? 9) - (b.score ?? 9);
  if (score !== 0) return score;
  const conf = (b.confidence ?? 0) - (a.confidence ?? 0);
  if (conf !== 0) return conf;
  return String(a.id).localeCompare(String(b.id));
}
