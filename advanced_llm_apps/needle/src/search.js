export function splitDocument(text) {
  const groups = text
    .replace(/\r\n/g, "\n")
    .split(/\n\s*\n/)
    .map((t) => t.trim())
    .filter(Boolean);
  const passages = [];
  for (let group of groups) {
    while (group.length > 1800) {
      let boundary = group.lastIndexOf(" ", 1800);
      if (boundary < 900) boundary = 1800;
      passages.push(group.slice(0, boundary));
      group = group.slice(boundary).trimStart();
    }
    if (group) passages.push(group);
  }
  return passages.map((text, i) => ({ id: `b${i}`, text }));
}
