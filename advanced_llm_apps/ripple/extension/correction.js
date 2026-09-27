// Loaded in both extension worlds so the bridge and review use the same rules.
const rippleCorrection = Object.freeze({
  matches(base, quote, replacement, actual) {
    if (typeof actual !== "string") return false;
    const at = base.indexOf(quote);
    if (!quote || at < 0 || base.indexOf(quote, at + 1) >= 0) return false;
    const prefix = base.slice(0, at),
      suffix = base.slice(at + quote.length);
    if (actual === prefix + replacement + suffix) return true;
    // Docs can collapse the spaces at a deletion/paste boundary. Only that
    // local edit may differ; every character outside it must remain intact.
    const left = prefix.replace(/[ \u00a0]+$/, ""),
      right = suffix.replace(/^[ \u00a0]+/, "");
    if (
      !actual.startsWith(left) ||
      !actual.endsWith(right) ||
      actual.length < left.length + right.length
    )
      return false;
    const expected =
      prefix.slice(left.length) +
      replacement +
      suffix.slice(0, suffix.length - right.length);
    const observed = actual.slice(left.length, actual.length - right.length);
    // Smart deletion also consumes the remaining separator when the removed
    // sentence starts/ends a paragraph. Keep the paragraph break itself exact.
    if (
      replacement === "" &&
      /^[ \u00a0]+$/.test(expected) &&
      observed === "" &&
      (!left || left.endsWith("\n") || !right || right.startsWith("\n"))
    )
      return true;
    const spaces = (text) => text.replace(/[ \u00a0]+/g, " ");
    return spaces(observed) === spaces(expected);
  },
});
