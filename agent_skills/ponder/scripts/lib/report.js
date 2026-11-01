// report.md and apply-plan.md.
//
// The report is the permanent record of the pondering: what was graded, what the engine
// advised, what the agent decided instead, and why. Overrides are surfaced forever
// (SPEC 4.2) and retractions are shown rather than erased (SPEC 8.2).

import { SEVERITY_RANK, EFFORT_RANK, describeDeltas, summariseDeltas, PERSPECTIVES } from './deltas.js';
import { coverageOf, countFindings, findingOrder } from './metrics.js';

const n = (v, d = 2) => (v === null || v === undefined || Number.isNaN(v) ? '—' : Number(v).toFixed(d));
const esc = (s) => String(s ?? '').replace(/\|/g, '\\|').replace(/\n+/g, ' ').trim();
const unitWord = (count, word) => `${word || 'unit'}${count === 1 ? '' : 's'}`;
/** "an 8-pass budget", "a 6-pass budget" — the report is a permanent record; it should read. */
const a = (v) => (/^(8|11|18)$/.test(String(v)) ? 'an' : 'a');

function unitLabelOf(units, id) {
  const u = units.find((x) => x.id === id);
  return u ? u.label : id;
}

function findingLine(f) {
  const bits = [
    `**${f.id}**`,
    f.severity,
    `score ${f.score}`,
    `confidence ${n(f.confidence)}`,
    `effort ${f.effort}`,
  ];
  if (f.dimension) bits.push(f.dimension);
  if (f.status !== 'open') bits.push(`_${f.status}_`);
  return bits.join(' · ');
}

/**
 * Build report.md.
 * `passes` is [{ pass, predict, deliberation, metrics, verdict, deltas }] in order.
 */
export function buildReport({ session, units, findings, ledger, passes, lens = null, generatedAt = new Date().toISOString() }) {
  const cov = coverageOf(units, findings);
  const counts = countFindings(findings);
  const live = findings.filter((f) => f.status !== 'retracted');
  const retracted = findings.filter((f) => f.status === 'retracted');
  const out = [];
  const last = passes.length ? passes[passes.length - 1] : null;

  out.push(`# Ponder — ${session.subject}`);
  out.push('');
  out.push(
    `\`${session.slug}\` · lens **${session.lens}** · status **${session.status}** · ${passes.length} pass${passes.length === 1 ? '' : 'es'} of ${a(session.maxPasses)} ${session.maxPasses}-pass budget · generated ${generatedAt}`,
  );
  out.push('');
  out.push('| | |');
  out.push('|---|---|');
  out.push(`| Subject | ${esc(session.subject)} |`);
  out.push(`| Lens | ${session.lens}${lens ? ` — unit = ${lens.unit}, ${lens.dimensions.length} dimensions` : ''} |`);
  out.push(`| Project | \`${session.project}\` |`);
  out.push(`| Passes | ${passes.length} run · min ${session.minPasses} · max ${session.maxPasses} |`);
  out.push(`| Coverage | ${n(cov.coverage)} — ${cov.graded} of ${cov.enumerated} ${unitWord(cov.enumerated, session.unitLabel)} graded |`);
  out.push(`| Findings | ${counts.total} total · ${counts.open} open · ${counts.resolved} resolved · ${counts.deferred || 0} deferred · ${counts.retracted} retracted |`);
  out.push(
    `| Final verdict | ${last && last.verdict ? `${last.verdict.verdict} (${last.verdict.reason}) → decided **${last.verdict.decision || 'undecided'}**` : 'not judged'} |`,
  );
  out.push(
    `| OCA | ${session.oca && session.oca.enabled ? (session.oca.reachable ? 'reachable' : 'enabled but unreachable') : 'off'}${session.oca && session.oca.sessionRef ? ` · ref ${session.oca.sessionRef}` : ''} |`,
  );
  out.push('');

  // --- convergence ---------------------------------------------------------
  out.push('## Convergence');
  out.push('');
  out.push('| Pass | Coverage | Novelty | Churn | Thrash | Surprise | Stall | Conf-floor | Voices | Advice | Decision |');
  out.push('|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|');
  for (const p of passes) {
    const m = p.metrics;
    const v = p.verdict;
    out.push(
      `| ${p.pass} | ${m ? n(m.coverage) : '—'} | ${m ? n(m.novelty) : '—'} | ${m ? n(m.churn) : '—'} | ${m ? n(m.thrash) : '—'} | ${m ? n(m.surprise) : '—'} | ${m ? m.stall : '—'} | ${m ? n(m.confidenceFloor) : '—'} | ${m ? m.voices : '—'} | ${v ? `${v.verdict} (${v.reason})` : '—'} | ${v && v.decision ? v.decision : '—'} |`,
    );
  }
  out.push('');
  out.push(
    '`—` on pass 1 is not a zero. Novelty, churn, thrash and surprise measure change against a previous pass, and pass 1 has none.',
  );
  out.push('');

  // --- overrides -----------------------------------------------------------
  out.push('## Overrides');
  out.push('');
  const overrides = passes.filter((p) => p.verdict && p.verdict.override);
  if (overrides.length === 0) {
    out.push('None. Every decision followed the engine\'s advice.');
  } else {
    for (const p of overrides) {
      out.push(
        `- **Pass ${p.pass}** — advice \`${p.verdict.verdict}\` (${p.verdict.reason}), decided \`${p.verdict.decision}\`.`,
      );
      out.push(`  > ${esc(p.verdict.why)}`);
    }
  }
  out.push('');

  // --- predictions ---------------------------------------------------------
  out.push('## Prediction vs reality');
  out.push('');
  out.push('| Pass | Predicted churn | Actual churn | Surprise | Claim |');
  out.push('|---:|---:|---:|---:|---|');
  for (const p of passes) {
    out.push(
      `| ${p.pass} | ${p.predict ? n(p.predict.churn) : '—'} | ${p.metrics ? n(p.metrics.churn) : '—'} | ${p.metrics ? n(p.metrics.surprise) : '—'} | ${esc(p.predict ? p.predict.claim : '')} |`,
    );
  }
  out.push('');

  // --- coverage ------------------------------------------------------------
  out.push('## Coverage');
  out.push('');
  out.push(`${cov.enumerated} ${unitWord(cov.enumerated, session.unitLabel)} enumerated, ${cov.graded} graded.`);
  out.push('');
  const cutFor = (id) => [...ledger].reverse().find((r) => r.op === 'unit-delete' && r.target === id) || null;
  const droppedUngraded = new Set(cov.removedUngraded);
  if (cov.ungraded.length) {
    out.push(`**Ungraded (${cov.ungraded.length}) — this session cannot honestly stop:**`);
    out.push('');
    for (const id of cov.ungraded) {
      const cut = droppedUngraded.has(id) ? cutFor(id) : null;
      out.push(
        `- \`${id}\` — ${esc(unitLabelOf(units, id))}${
          cut
            ? ` · **deleted ungraded** in pass ${cut.pass} by the ${cut.perspective || 'engine'}: ${esc(cut.why)} · a delete cannot manufacture coverage, so it still counts`
            : ''
        }`,
      );
    }
    out.push('');
  }
  if (cov.removedAppraised.length) {
    // Coverage is measured against what is left in scope, so an appraised unit dropped from
    // the inventory moves the number. Name every one, with the pass and the reason, or the
    // ratio above is a claim nobody can audit.
    out.push(
      `**Removed from the inventory (${cov.removedAppraised.length}) — appraised, then dropped, so coverage above is measured against what is left:**`,
    );
    out.push('');
    for (const id of cov.removedAppraised) {
      const cut = cutFor(id);
      out.push(
        `- \`${id}\` — ${esc(unitLabelOf(units, id))}${cut ? ` · removed in pass ${cut.pass} by the ${cut.perspective || 'engine'}: ${esc(cut.why)}` : ''}`,
      );
    }
    out.push('');
  }
  // Corrected units. A unit-edit is a revision like any other and gets the same treatment a
  // removal gets: named, with the pass, the perspective and the why. A stale label silently
  // fixed is a caption nobody can audit, and a moved `path` is what a phantom claim would
  // have been checked against — both belong on the permanent record (SPEC 3.4, SPEC 3.5).
  const edits = ledger.filter((r) => r && r.op === 'unit-edit' && r.set && typeof r.set === 'object');
  if (edits.length) {
    out.push(`### Corrected ${unitWord(edits.length, session.unitLabel)}`);
    out.push('');
    out.push(
      `${edits.length} ${unitWord(edits.length, session.unitLabel)} ${edits.length === 1 ? 'was' : 'were'} corrected in place by a \`unit-edit\`. Correcting a unit changes nothing about coverage — it is neither an addition nor a removal — but it is a revision, so it is on the ledger and it counts toward churn.`,
    );
    out.push('');
    for (const e of edits) {
      const fields = Object.keys(e.set);
      out.push(
        `- \`${e.target}\` — ${esc(unitLabelOf(units, e.target))} · pass ${e.pass} · ${fields.join(', ')} corrected by the ${e.perspective || 'engine'}`,
      );
      for (const f of fields) {
        out.push(`  - \`${f}\` → ${typeof e.set[f] === 'string' ? esc(e.set[f]) : `\`${esc(JSON.stringify(e.set[f]))}\``}`);
      }
      out.push(`  > ${esc(e.why)}`);
    }
    out.push('');
  }
  if (cov.phantoms.length) {
    // Every accepted phantom is permanent, individually justified, and shows what the
    // engine was able to check. An unverified claim is the one that has to stand out.
    // SPEC 3.5 keeps two unverified claims apart, and the summary sentence has to keep them
    // apart too: a unit with no path was never checkable, while a unit whose path was edited
    // had every version of it checked and none existed — the engine simply will not certify
    // an absence about a target that moved. Wording the summary off the unverified count
    // alone made it announce "the unit had no path" over a per-item line saying the opposite.
    const unverifiedPhantoms = cov.phantoms.filter((p) => p.verification !== 'verified-missing');
    const unverified = unverifiedPhantoms.length;
    const movedCount = unverifiedPhantoms.filter((p) => {
      const cut = cutFor(p.id);
      return cut && Array.isArray(cut.pathsChecked) && cut.pathsChecked.length > 0;
    }).length;
    const noPathCount = unverified - movedCount;
    const one = cov.phantoms.length === 1;
    const reason =
      movedCount === 0
        ? `${unverified === 1 ? 'it had' : 'they had'} no path to check the claim against`
        : noPathCount === 0
          ? `${unverified === 1 ? 'its path was' : 'their paths were'} edited, and every version was checked and missing — but the engine does not certify an absence about a target that moved`
          : `${noPathCount} had no path, and ${movedCount} had a path that moved`;
    const clause =
      unverified === 0
        ? ''
        : unverified === cov.phantoms.length
          ? ` The engine could not check ${one ? 'it' : 'any of them'}: ${reason}.`
          : ` ${unverified} of them could not be checked: ${reason}.`;
    out.push(`### Phantom units`);
    out.push('');
    out.push(
      `${cov.phantoms.length} ${unitWord(cov.phantoms.length, session.unitLabel)} ${one ? 'was' : 'were'} claimed not to exist in the software and dropped from the coverage denominator.${clause}`,
    );
    out.push('');
    for (const ph of cov.phantoms) {
      const cut = cutFor(ph.id);
      const verified = ph.verification === 'verified-missing';
      const unit = units.find((u) => u.id === ph.id) || null;
      // Two different unverified claims, and the report must not conflate them: a unit with
      // no path was never checkable, while a unit whose path was edited had every version of
      // it checked and none of them existed — the engine still refuses to certify an absence
      // about a target that moved (SPEC 3.5).
      const movedPaths = cut && Array.isArray(cut.pathsChecked) ? cut.pathsChecked : null;
      const mark = verified
        ? `verified-missing${unit && unit.phantomPath ? ` (\`${unit.phantomPath}\` does not exist)` : ''}`
        : movedPaths
          ? `**UNVERIFIED — this unit's path was edited, so the engine checked every version of it (${movedPaths.map((p) => `\`${p}\``).join(', ')}) and found none, but it will not certify an absence about a target that moved**`
          : '**UNVERIFIED — this unit had no path, so the claim could not be checked**';
      out.push(
        `- \`${ph.id}\` — ${esc(unitLabelOf(units, ph.id))} · pass ${ph.pass ?? (cut ? cut.pass : '?')} · ${mark}`,
      );
      if (cut) out.push(`  > ${esc(cut.why)}`);
    }
    out.push('');
  }

  // --- findings ------------------------------------------------------------
  out.push('## Findings');
  out.push('');
  const byUnit = new Map();
  for (const f of live) {
    if (!byUnit.has(f.unit)) byUnit.set(f.unit, []);
    byUnit.get(f.unit).push(f);
  }
  const unitOrder = units
    .filter((u) => byUnit.has(u.id))
    .sort((a, b) => {
      const best = (id) => Math.min(...byUnit.get(id).map((f) => SEVERITY_RANK[f.severity] ?? 9));
      return best(a.id) - best(b.id) || String(a.id).localeCompare(String(b.id));
    });
  // findings whose unit vanished from the inventory still get reported
  for (const id of byUnit.keys()) {
    if (!units.some((u) => u.id === id)) unitOrder.push({ id, label: id, path: null });
  }
  if (unitOrder.length === 0) out.push('_No standing findings._');
  for (const u of unitOrder) {
    const list = byUnit.get(u.id).sort(findingOrder);
    out.push(`### ${u.label} \`${u.id}\``);
    if (u.path) out.push(`\`${u.path}\``);
    if (u.removedInPass) out.push(`_Removed from the inventory in pass ${u.removedInPass}._`);
    out.push('');
    for (const f of list) {
      out.push(`- ${findingLine(f)} — ${esc(f.title)}`);
      if (f.detail) out.push(`  ${esc(f.detail)}`);
      if (f.evidence && f.evidence.length) out.push(`  Evidence: ${f.evidence.map((e) => `\`${e}\``).join(', ')}`);
      if (f.recommendation) out.push(`  Do: ${esc(f.recommendation)}`);
      if (f.history && f.history.length) {
        const touches = f.history.map((h) => `p${h.pass} ${h.op} ${h.field}`).join(', ');
        out.push(`  _Revised: ${touches}_`);
      }
      out.push('');
    }
  }

  // --- retractions ---------------------------------------------------------
  out.push('## Retracted');
  out.push('');
  if (retracted.length === 0) {
    out.push('Nothing was retracted.');
  } else {
    out.push('Retraction is a state, not an erasure — a later pass can reverse any of these.');
    out.push('');
    for (const f of retracted.sort(findingOrder)) {
      const kill = [...ledger].reverse().find((r) => r.op === 'delete' && r.target === f.id);
      out.push(
        `- \`${f.id}\` (${f.unit}) — ${esc(f.title)}${kill ? ` · retracted in pass ${kill.pass} by the ${kill.perspective || 'engine'}: ${esc(kill.why)}` : ''}`,
      );
    }
  }
  out.push('');

  // --- deliberation --------------------------------------------------------
  out.push('## Deliberation');
  out.push('');
  for (const p of passes) {
    const d = p.deliberation;
    out.push(`### Pass ${p.pass}`);
    out.push('');
    if (!d) {
      out.push('_No deliberation recorded._');
      out.push('');
      continue;
    }
    if (d.skipped) {
      out.push(`_Skipped._ ${esc(d.why)}`);
      out.push('');
      continue;
    }
    for (const name of PERSPECTIVES) {
      const arg = d.perspectives ? d.perspectives[name] : null;
      if (!arg) continue;
      out.push(
        `- **${name}**${typeof arg.confidence === 'number' ? ` (confidence ${n(arg.confidence)})` : ''} — ${esc(arg.argument)}`,
      );
    }
    const missing = PERSPECTIVES.filter((name) => !d.perspectives || !d.perspectives[name]);
    if (missing.length) out.push(`- _Silent: ${missing.join(', ')}._`);
    // The pass-1 seeding is not something the deliberation resolved; count it separately.
    const seeded = (p.deltas || []).filter((d) => d.source === 'grade').length;
    const argued = (p.deltas || []).filter((d) => d.source !== 'grade');
    out.push('');
    out.push(
      `Resolution: ${describeDeltas(summariseDeltas(argued))}${seeded ? ` (plus ${seeded} findings seeded by \`ponder grade\` before the argument)` : ''}.`,
    );
    out.push('');
  }

  // --- ledger --------------------------------------------------------------
  const total = summariseDeltas(ledger);
  out.push('## Ledger');
  out.push('');
  out.push(`${total.total} deltas across ${passes.length} pass${passes.length === 1 ? '' : 'es'}: ${describeDeltas(total)}.`);
  out.push('');
  out.push('| Pass | Deltas | Perspectives |');
  out.push('|---:|---|---|');
  for (const p of passes) {
    const s = summariseDeltas(p.deltas || []);
    out.push(`| ${p.pass} | ${describeDeltas(s)} | ${s.voices.join(', ') || '—'} |`);
  }
  out.push('');
  out.push('The full append-only record is `ledger.jsonl`.');
  out.push('');
  out.push('---');
  out.push('');
  out.push('*Generated by [Ponder](https://github.com/Quinnod345/ponder) — AI that knows when to speak, and when to shut up.*');
  out.push('');

  return out.join('\n');
}

/** Findings the apply plan will carry: open, at or above the severity floor. */
export function selectApplyFindings(findings, severityFloor = 'must') {
  const floor = SEVERITY_RANK[severityFloor];
  return findings
    .filter((f) => f.status === 'open' && (SEVERITY_RANK[f.severity] ?? 9) <= floor)
    .sort((a, b) => {
      const s = (SEVERITY_RANK[a.severity] ?? 9) - (SEVERITY_RANK[b.severity] ?? 9);
      if (s !== 0) return s;
      const score = (a.score ?? 9) - (b.score ?? 9);
      if (score !== 0) return score;
      const eff = (EFFORT_RANK[a.effort] ?? 9) - (EFFORT_RANK[b.effort] ?? 9);
      if (eff !== 0) return eff;
      return String(a.id).localeCompare(String(b.id));
    });
}

/** Parse `--severity must,should` into a floor. The lowest severity named wins. */
export function severityFloorFrom(value) {
  const names = String(value || 'must')
    .split(',')
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
  let floor = null;
  for (const name of names) {
    if (!(name in SEVERITY_RANK)) return { error: name };
    if (floor === null || SEVERITY_RANK[name] > SEVERITY_RANK[floor]) floor = name;
  }
  return { floor: floor || 'must', names };
}

/**
 * Build apply-plan.md: an ordered work plan grouped by unit.
 * Ponder never edits the subject's source — this is what it hands the agent instead.
 */
export function buildApplyPlan({ session, units, findings, severityFloor = 'must', generatedAt = new Date().toISOString() }) {
  const selected = selectApplyFindings(findings, severityFloor);
  const groups = [];
  const seen = new Map();
  for (const f of selected) {
    if (!seen.has(f.unit)) {
      const unit = units.find((u) => u.id === f.unit) || { id: f.unit, label: f.unit, path: null };
      const group = { unit, findings: [] };
      seen.set(f.unit, group);
      groups.push(group);
    }
    seen.get(f.unit).findings.push(f);
  }

  const out = [];
  out.push(`# Apply plan — ${session.subject}`);
  out.push('');
  out.push(
    `\`${session.slug}\` · lens **${session.lens}** · ${selected.length} open finding${selected.length === 1 ? '' : 's'} at severity **${severityFloor}** or above · generated ${generatedAt}`,
  );
  out.push('');
  if (selected.length === 0) {
    out.push(`Nothing open at severity ${severityFloor} or above. There is no work to do at this bar.`);
    out.push('');
    return { markdown: out.join('\n'), selected, groups };
  }
  out.push('Work top to bottom. Ponder does not edit source — this plan is the handoff.');
  out.push('');
  let i = 0;
  for (const g of groups) {
    i++;
    out.push(`## ${i}. ${g.unit.label} \`${g.unit.id}\``);
    if (g.unit.path) out.push(`\`${g.unit.path}\``);
    out.push('');
    for (const f of g.findings) {
      out.push(`- [ ] **${f.id} · ${f.severity} · score ${f.score} · effort ${f.effort}** — ${esc(f.title)}`);
      if (f.detail) out.push(`      ${esc(f.detail)}`);
      if (f.evidence && f.evidence.length) out.push(`      Evidence: ${f.evidence.map((e) => `\`${e}\``).join(', ')}`);
      out.push(`      Do: ${esc(f.recommendation || 'No recommendation was written. Decide the fix from the detail above.')}`);
    }
    out.push('');
  }
  const byEffort = {};
  for (const f of selected) byEffort[f.effort] = (byEffort[f.effort] || 0) + 1;
  out.push('## Shape of the work');
  out.push('');
  out.push(
    `${groups.length} ${unitWord(groups.length, session.unitLabel)} · ${selected.length} finding${selected.length === 1 ? '' : 's'} · effort ${Object.entries(byEffort)
      .sort((a, b) => (EFFORT_RANK[a[0]] ?? 9) - (EFFORT_RANK[b[0]] ?? 9))
      .map(([k, v]) => `${v}×${k}`)
      .join(', ')}`,
  );
  out.push('');
  out.push('---');
  out.push('');
  out.push('*Generated by [Ponder](https://github.com/Quinnod345/ponder) — AI that knows when to speak, and when to shut up.*');
  out.push('');
  return { markdown: out.join('\n'), selected, groups };
}
