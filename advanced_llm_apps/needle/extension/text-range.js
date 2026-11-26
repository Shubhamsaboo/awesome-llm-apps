// Convert server offsets into a DOM range, including sentences across inline tags.
globalThis.NeedleTextRange = (element, focus, expectedText) => {
  const raw = element.textContent;
  if (
    raw.trim() !== expectedText ||
    !focus ||
    expectedText.slice(focus.start, focus.end) !== focus.text
  )
    return null;
  const padding = raw.length - raw.trimStart().length;
  const start = padding + focus.start,
    end = padding + focus.end;
  if (start < 0 || end <= start || end > raw.length) return null;
  const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
  let offset = 0,
    startNode = null,
    endNode = null,
    startOffset = 0,
    endOffset = 0,
    node;
  while ((node = walker.nextNode())) {
    const next = offset + node.textContent.length;
    if (!startNode && start < next) {
      startNode = node;
      startOffset = start - offset;
    }
    if (end <= next) {
      endNode = node;
      endOffset = end - offset;
      break;
    }
    offset = next;
  }
  if (!startNode || !endNode) return null;
  const range = new Range();
  range.setStart(startNode, startOffset);
  range.setEnd(endNode, endOffset);
  return range;
};
