// Offsets refer to the unchanged source string (UTF-16, as used by DOM ranges).
const segmenter = new Intl.Segmenter("en", { granularity: "sentence" });
export function sentenceSpans(text) {
  return [...segmenter.segment(text)]
    .map(({ segment, index }) => {
      const start = index + segment.length - segment.trimStart().length;
      const end = index + segment.trimEnd().length;
      return { start, end, text: text.slice(start, end) };
    })
    .filter((s) => s.end > s.start);
}
