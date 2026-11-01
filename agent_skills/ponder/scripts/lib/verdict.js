// Verdicts: the engine's convergence advice (SPEC 4.1) and the rules governing the agent's
// committed decision (SPEC 4.2).
//
// The engine advises. The agent decides. The one thing the agent cannot do is stop while a
// unit has never been graded — that gate has no override flag, and it is the reason ponder
// exists.

import { userError, stateError } from './session.js';

export const VERDICTS = ['continue', 'stop', 'escalate', 'blocked'];
export const DECISIONS = ['continue', 'stop', 'escalate'];

export const THRASH_LIMIT = 0.25;
export const CONFIDENCE_FLOOR_LIMIT = 0;
export const CONVERGED_NOVELTY = 0.05;
export const CONVERGED_CHURN = 0.1;
export const MIN_VOICES = 3;
export const MIN_OVERRIDE_WHY = 12;

const STRONG_OBSERVATION = new Set(['high', 'critical', 'severe', 'urgent']);

/** Metrics are stored at 4 decimals; messages read better at 2. */
const n2 = (v) => (v === null || v === undefined || Number.isNaN(v) ? '—' : Number(v).toFixed(2));

/** "an 8-pass budget", "a 6-pass budget" — these strings end up in permanent records. */
const a = (v) => (/^(8|11|18)$/.test(String(v)) ? 'an' : 'a');

function observationIsStrong(o) {
  if (!o || typeof o !== 'object') return false;
  const sev = o.severity ?? o.severity_level ?? null;
  if (typeof sev === 'string' && STRONG_OBSERVATION.has(sev.toLowerCase())) return true;
  if (typeof sev === 'number' && sev >= 0.7) return true;
  return false;
}

/**
 * The ordered verdict rules. First match wins.
 *
 * `observations` are open OCA metacognitive observations for this session; they act only as
 * a tie-breaker on rule 8 (the otherwise-continue case), never as a way past the coverage
 * gate and never as a way to overturn a rule that actually matched.
 */
export function computeVerdict({ metrics, session, priorMetrics = [], observations = null }) {
  const pass = Number(metrics.pass);
  const notes = [];

  // 1. coverage gate — absolute. The ungraded list is authoritative alongside the ratio,
  // so a rounded 1.0000 over a large inventory can never open the gate.
  const ungradedCount = Array.isArray(metrics.ungraded) ? metrics.ungraded.length : 0;
  const enumerated = Number(metrics.units && metrics.units.enumerated) || 0;
  const removedUngraded = Array.isArray(metrics.removedUngraded) ? metrics.removedUngraded : [];
  if (metrics.coverage < 1 || ungradedCount > 0) {
    return {
      verdict: 'blocked',
      reason: 'coverage',
      rule: 1,
      ungraded: metrics.ungraded,
      removedUngraded,
      // An inventory emptied by unit-delete deltas is a different problem from ungraded
      // units, and "0 of 0 have never been graded" tells the agent nothing it can act on.
      message:
        enumerated === 0
          ? `the inventory is empty — there is nothing left to have coverage over. Coverage over zero ${plural(session.unitLabel, 2)} is not a pondering.`
          : `${ungradedCount} of ${enumerated} ${plural(session.unitLabel, ungradedCount)} ${ungradedCount === 1 ? 'has' : 'have'} never been graded. Stopping is not permitted.`,
      notes:
        enumerated === 0
          ? [...notes, `put a ${session.unitLabel || 'unit'} back with a unit-add delta, or close this session with ponder abort --why "<reason>".`]
          : [...notes, ...removedUngradedNotes(removedUngraded, session)],
    };
  }

  // 2. a single pass is an opinion, not a pondering.
  if (pass < Number(session.minPasses)) {
    return {
      verdict: 'continue',
      reason: 'min-passes',
      rule: 2,
      ungraded: [],
      message: `pass ${pass} of ${a(session.minPasses)} ${session.minPasses}-pass minimum. One pass is an opinion, not a pondering.`,
      notes,
    };
  }

  // 3. oscillation. Guarded on thrash being a real number: pass 1 has none, and a null
  // that coerced to 0 would read as a healthy pass rather than as an absent signal.
  if (typeof metrics.thrash === 'number' && metrics.thrash > THRASH_LIMIT) {
    return {
      verdict: 'escalate',
      reason: 'thrash',
      rule: 3,
      ungraded: [],
      message: `thrash ${n2(metrics.thrash)} is above ${THRASH_LIMIT} — the loop is reversing itself. Another identical pass will not help.`,
      notes,
    };
  }

  // Stillness is not understanding. Every important call must clear its evidence
  // confidence floor, and both quiet passes must actually hear adversarial review.
  const uncertainty = metrics.confidenceFloor > CONFIDENCE_FLOOR_LIMIT;
  const missingVoices = Number(metrics.voices || 0) < MIN_VOICES;
  if (uncertainty || missingVoices) {
    const exhausted = pass >= Number(session.maxPasses);
    const stalled = Number(metrics.stall) >= 2;
    return {
      verdict: exhausted ? 'stop' : stalled ? 'escalate' : 'continue',
      reason: exhausted ? 'budget' : uncertainty ? 'low-confidence' : 'insufficient-perspectives',
      rule: exhausted ? 7 : 5, ungraded: [],
      message: exhausted
        ? 'The pass budget is exhausted with unresolved review uncertainty. This is a budget stop, not convergence.'
        : uncertainty
          ? `${Math.round(metrics.confidenceFloor * 100)}% of open must-severity findings are below 0.5 confidence. Gather evidence; quiet repetition cannot resolve uncertainty.`
          : `Only ${metrics.voices || 0} perspectives reviewed this pass. Hear at least ${MIN_VOICES} before claiming convergence.`,
      notes: stalled ? ['The answer stopped moving while review was incomplete; change the evidence or the reviewing perspective.'] : [],
    };
  }

  // 6. two consecutive quiet passes.
  const quiet = (m) =>
    m && Number(m.voices || 0) >= MIN_VOICES && m.confidenceFloor === 0 && typeof m.novelty === 'number' && typeof m.churn === 'number' && m.novelty < CONVERGED_NOVELTY && m.churn < CONVERGED_CHURN;
  const previous = priorMetrics.find((m) => m && Number(m.pass) === pass - 1);
  if (quiet(metrics) && quiet(previous)) {
    return {
      verdict: 'stop',
      reason: 'converged',
      rule: 6,
      ungraded: [],
      message: `novelty ${n2(metrics.novelty)} and churn ${n2(metrics.churn)}, two passes running. Further passes stopped changing the answer.`,
      notes,
    };
  }

  // 4. perseveration. `stall` only ever counts passes whose churn was a number, so a pass
  // with no churn at all cannot contribute to it.
  if (Number(metrics.stall) >= 2 && metrics.coverage >= 1) {
    return {
      verdict: 'stop',
      reason: 'perseveration',
      rule: 4,
      ungraded: [],
      message: `${metrics.stall} consecutive passes moved almost nothing (churn ${n2(metrics.churn)}). Further passes are theatre.`,
      notes,
    };
  }

  // 7. budget.
  if (pass >= Number(session.maxPasses)) {
    return {
      verdict: 'stop',
      reason: 'budget',
      rule: 7,
      ungraded: [],
      message: `pass ${pass} of ${a(session.maxPasses)} ${session.maxPasses}-pass budget. This is a budget stop, not convergence.`,
      notes,
    };
  }

  // 8. otherwise keep going — unless the OCA is holding open observations about this loop.
  const strong = Array.isArray(observations) ? observations.filter(observationIsStrong) : [];
  if (strong.length > 0) {
    return {
      verdict: 'escalate',
      reason: 'oca-observations',
      rule: 8,
      ungraded: [],
      message: `${strong.length} open metacognitive observation${strong.length === 1 ? '' : 's'} on this loop tip an otherwise-continue into escalate.`,
      notes: strong.map((o) => `${o.observation_type || o.type || 'observation'}: ${o.description || ''}`.trim()),
    };
  }

  // SPEC 4: the relative signals are null on pass 1, so rule 8 cannot read movement off
  // them there. Saying "the finding set is still moving" from two dashes would be the
  // engine asserting exactly what it just declined to measure.
  const measured = metrics && typeof metrics.novelty === 'number' && typeof metrics.churn === 'number';
  return {
    verdict: 'continue',
    reason: 'default',
    rule: 8,
    ungraded: [],
    message: !measured
      ? 'this pass created the baseline — there is no previous pass to measure movement against yet.'
      : quiet(metrics)
        ? `novelty ${n2(metrics.novelty)}, churn ${n2(metrics.churn)} — one quiet pass. Convergence needs two in a row.`
        : `novelty ${n2(metrics.novelty)}, churn ${n2(metrics.churn)} — the finding set is still moving.`,
    notes,
  };
}

function plural(word, count = 2) {
  const w = word || 'unit';
  if (count === 1) return w;
  return /s$/.test(w) ? w : `${w}s`;
}

/**
 * The lines that separate a merely-ungraded unit from one that was deleted without ever
 * being appraised (SPEC 4). Both block a stop; only the second needs explaining, because
 * the agent has already tried to make it go away.
 */
export function removedUngradedNotes(ids, session) {
  if (!Array.isArray(ids) || ids.length === 0) return [];
  const one = ids.length === 1;
  const word = plural(session && session.unitLabel, ids.length);
  return [
    one
      ? `${ids[0]} is already out of the inventory. It was deleted without ever being graded, and a delete cannot manufacture coverage, so it still counts.`
      : `${ids.length} of those ${word} are already out of the inventory: ${ids.join(', ')}. They were deleted without ever being graded, and a delete cannot manufacture coverage, so they still count.`,
    `Two honest ways out: grade ${one ? 'it' : 'them'} after a unit-add delta puts ${one ? 'it' : 'them'} back, or — if ${one ? 'it does' : 'they do'} not exist in the software at all — delete ${one ? 'it' : 'them'} again with "phantom": true and let the engine check the claim against the path.`,
  ];
}

/**
 * Check the agent's committed decision against the advice (SPEC 4.2).
 *
 * Throws:
 *  - stateError (exit 2) for `stop` while coverage < 1.0. No flag overrides this.
 *  - userError  (exit 1) for an unknown decision, a missing --why, or an override whose
 *    --why is shorter than 12 characters.
 *
 * Returns { override, warnings } otherwise. `coverage` is recomputed live by the caller
 * rather than trusted from metrics.json, so the gate cannot be beaten by a stale judge.
 */
export function checkDecision({ session, decision, why, advice, adviceReason = null, metrics, coverage, ungraded, enumerated = null, removedUngraded = [] }) {
  if (!DECISIONS.includes(decision)) {
    throw userError(`"${decision}" is not a decision — use ${DECISIONS.join(', ')}.`);
  }
  const reason = typeof why === 'string' ? why.trim() : '';
  if (reason === '') {
    throw userError('a decision needs --why "<reason>". The reason is written to the report permanently.');
  }

  if (decision === 'stop' && (coverage < 1 || ungraded.length > 0)) {
    if (enumerated === 0) {
      throw stateError(
        `cannot stop: the inventory is empty, so there is nothing for coverage to be about.`,
        [
          `every ${session.unitLabel || 'unit'} has been removed from units.json by unit-delete deltas.`,
          'There is no override for this. Put one back, or close the session unfinished:',
          `  ponder delta --file deltas.jsonl --session ${session.slug}   # a unit-add delta`,
          `  ponder abort --why "<reason>" --session ${session.slug}`,
        ],
      );
    }
    const dropped = new Set(Array.isArray(removedUngraded) ? removedUngraded : []);
    throw stateError(
      `cannot stop: coverage is ${coverage.toFixed(2)}, not 1.0. ${ungraded.length} ${plural(session.unitLabel, ungraded.length)} ${ungraded.length === 1 ? 'has' : 'have'} never been graded.`,
      [
        // The two kinds are named apart on the same list, so an agent that tried deleting
        // its way out sees exactly which deletes did not buy it anything.
        ...ungraded.map((id) => (dropped.has(id) ? `${id}  (deleted ungraded — still counts)` : id)),
        '',
        ...removedUngradedNotes([...dropped], session),
        ...(dropped.size ? [''] : []),
        `There is no override for this. Grade ${ungraded.length === 1 ? 'it' : 'them'}, then judge again:`,
        `  ponder delta --file deltas.jsonl --session ${session.slug}`,
      ],
    );
  }

  const blocked = advice === 'blocked';
  // Belt and braces on SPEC 4.2: `blocked` is the one advice a stop may never override.
  // Live coverage above is the substantive gate; this catches the case where the pass was
  // judged blocked and the finding set has been changed underneath the verdict since.
  if (decision === 'stop' && blocked) {
    throw stateError(
      `cannot stop: pass ${metrics.pass} was judged blocked, and blocked is the one advice a stop may not override.`,
      [
        'the coverage recorded at judge time and the coverage now disagree.',
        `decide continue and let the next pass judge it honestly:  ponder decide continue --why "<reason>" --session ${session.slug}`,
      ],
    );
  }
  const override = blocked ? false : decision !== advice;
  if (override && reason.length < MIN_OVERRIDE_WHY) {
    throw userError(
      `overriding the "${advice}" advice with "${decision}" needs a --why of at least ${MIN_OVERRIDE_WHY} characters (got ${reason.length}).`,
      ['The override and its reason are surfaced permanently under Overrides in report.md.'],
    );
  }

  const warnings = [];
  // `voices` is who spoke in the deliberation, not who emitted a delta. A perspective that
  // argued "nothing to change here" has spoken; the old delta count made every genuine
  // convergence — where one delta is all the churn budget allows — look like a silent pass.
  if (decision === 'stop' && Number(metrics.voices) < MIN_VOICES) {
    warnings.push(
      metrics.deliberationSkipped
        ? `this pass skipped deliberation entirely. A pass that never argued with itself is a weak place to stop.`
        : `this pass heard ${metrics.voices} of 4 perspectives (${(metrics.voiceNames || []).join(', ') || 'none'}). A pass that heard fewer than ${MIN_VOICES} is a weak place to stop.`,
    );
  }
  if (decision === 'stop' && advice === 'stop' && adviceReason === 'budget') {
    warnings.push('this is a budget stop, not convergence. report.md will say so.');
  }
  if (blocked && decision === 'escalate') {
    warnings.push('escalating while blocked is legal, but coverage still has to reach 1.0 before this session can stop.');
  }
  return { override, warnings, reason };
}

/** The session status a `stop` decision produces. Only rule 6 earns "converged". */
export function statusAfterStop(advice, adviceReason) {
  return advice === 'stop' && adviceReason === 'converged' ? 'converged' : 'stopped';
}

/** One-line human summary of a verdict for status and report. */
export function verdictSummary(v) {
  if (!v) return 'not judged yet';
  const decided = v.decision ? `decided ${v.decision}` : 'undecided';
  return `${v.verdict} (${v.reason}) — ${decided}`;
}
