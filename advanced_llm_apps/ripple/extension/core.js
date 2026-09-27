// Pure document logic. No browser state, credentials, or model calls.
export function sentences(text) {
  const segmenter = new Intl.Segmenter("en", { granularity: "sentence" });
  let offset = 0,
    index = 0;
  const out = [];
  for (const paragraph of text.split("\n")) {
    for (const part of segmenter.segment(paragraph)) {
      const leading = part.segment.length - part.segment.trimStart().length;
      const value = part.segment.trim();
      if (value)
        out.push({
          id: `b0s${index++}`,
          text: value,
          section: "",
          start: offset + part.index + leading,
          end: offset + part.index + leading + value.length,
        });
    }
    offset += paragraph.length + 1;
  }
  return out;
}
export function diff(before, after) {
  if (before === after) return null;
  let start = 0,
    tail = 0;
  while (
    start < before.length &&
    start < after.length &&
    before[start] === after[start]
  )
    start++;
  while (
    tail < before.length - start &&
    tail < after.length - start &&
    before[before.length - 1 - tail] === after[after.length - 1 - tail]
  )
    tail++;
  const prior = sentences(before),
    next = sentences(after);
  const oldEnd = before.length - tail,
    newEnd = after.length - tail;
  let oldParts = prior.filter((s) => s.end > start && s.start < oldEnd);
  let newParts = next.filter((s) => s.end > start && s.start < newEnd);
  if (
    oldEnd === start &&
    newParts.some((s) => s.start < start || s.end > newEnd)
  )
    oldParts = prior.filter((s) => s.start <= start && s.end >= start);
  if (
    newEnd === start &&
    oldParts.some((s) => s.start < start || s.end > oldEnd)
  )
    newParts = next.filter((s) => s.start <= start && s.end >= start);
  const first = oldParts[0]?.start ?? start;
  const last = oldParts.at(-1)?.end ?? oldEnd;
  const nextFirst = newParts[0]?.start ?? start;
  const nextLast = newParts.at(-1)?.end ?? newEnd;
  return {
    before: before.slice(first, last).trim(),
    after: after.slice(nextFirst, nextLast).trim(),
    start: nextFirst,
    end: nextLast,
  };
}
export function fingerprint(value) {
  let n = 2166136261;
  for (let i = 0; i < value.length; i++)
    n = Math.imul(n ^ value.charCodeAt(i), 16777619);
  return (n >>> 0).toString(36);
}
export function candidates(text, source) {
  return sentences(text)
    .filter((s) => s.end <= source.start || s.start >= source.end)
    .map(({ id, text, section }) => ({ id, text, section }));
}
export function uniqueSpan(text, quote) {
  const start = text.indexOf(quote);
  return start < 0 || text.indexOf(quote, start + 1) >= 0
    ? null
    : { start, end: start + quote.length };
}
export function normalize(text) {
  return text
    .replace(/\u0003/g, "")
    .replace(/\u00a0/g, " ")
    .replace(/[ \t]+/g, " ")
    .replace(/\r\n/g, "\n")
    .trim();
}
export function reconcile(previous, current, sources, findings = []) {
  const change = diff(previous, current);
  if (!change) return sources;
  const kept = sources.filter(
    (s) =>
      !(uniqueSpan(current, s.before) && !uniqueSpan(current, s.after)) &&
      !(
        change.before.includes(s.after) &&
        !change.after &&
        !uniqueSpan(current, s.after)
      ),
  );
  const existing = kept.find((s) => change.before === s.after);
  if (existing)
    return kept
      .map((s) => (s === existing ? { ...s, after: change.after } : s))
      .filter((s) => s.after && s.before !== s.after);
  // Correcting a marked sentence is a repair, not a new governing fact.
  const repair = findings.some(
    (f) => change.before.includes(f.text) || f.text.includes(change.before),
  );
  if (
    repair ||
    !change.before ||
    !change.after ||
    change.before === change.after
  )
    return kept;
  if (kept.length < sources.length) return kept; // Undo of a tracked source.
  if (change.before.length > 3000 || change.after.length > 3000)
    throw new Error(
      "That edit is too large to check. Pause and resume Ripple, then change one fact at a time.",
    );
  if (kept.length >= 4)
    throw new Error(
      "Four changes are being tracked. Finish reviewing them, then pause and resume for a fresh baseline.",
    );
  return [
    ...kept,
    {
      id: fingerprint(change.before + "\0" + change.after),
      before: change.before,
      after: change.after,
    },
  ];
}
