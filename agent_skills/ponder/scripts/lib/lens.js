// Lens packs: `lenses/<name>.md`, YAML front matter plus prose (SPEC 7).
//
// The front-matter parser is hand-rolled and deliberately small. It supports exactly the
// shapes the lens contract uses:
//
//   key: scalar                 strings, numbers, booleans, null
//   key: [a, b, c]              flow sequences, single- or multi-line
//   key: |                      block scalars (and `>` folded scalars)
//   key:                        nested mappings and `- ` block sequences
//     nested: value
//
// Anything richer than that is a lens pack doing something the contract does not ask for,
// and it is reported as a parse error rather than silently half-read.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { userError } from './session.js';
import { termCols, wrap } from './fmt.js';

export const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

export function lensDir() {
  const override = process.env.PONDER_LENS_DIR;
  return override && override.trim() !== '' ? path.resolve(override) : path.join(REPO_ROOT, 'lenses');
}

/**
 * Lens names installed on disk, sorted.
 *
 * Files starting with `_` are templates and examples, not lenses to open a session with —
 * `_custom-template.md` is the worked example a custom rubric is copied from, and offering
 * it as an installed lens sends agents down a path where `session.lens` records the
 * template's own front-matter name and nothing can reload it. `--lens _name` still works if
 * someone means it; this is only what ponder advertises.
 */
export function availableLenses() {
  try {
    return fs
      .readdirSync(lensDir())
      .filter((f) => f.endsWith('.md') && !f.startsWith('_'))
      .map((f) => f.slice(0, -3))
      .sort();
  } catch {
    return [];
  }
}

// ---------------------------------------------------------------------------
// front matter
// ---------------------------------------------------------------------------

const indentOf = (line) => line.length - line.replace(/^\s*/, '').length;

/**
 * Drop a trailing `#` comment from one line of YAML *structure*.
 *
 * Only parseRegion calls this, and only on lines it is reading as structure. Never call it
 * on block-scalar content: `enumerate:` holds commands, and ` #` is a legal character in
 * every one of them.
 */
function stripComment(text) {
  let out = '';
  let quote = null;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quote) {
      out += ch;
      if (ch === quote && text[i - 1] !== '\\') quote = null;
      continue;
    }
    if (ch === '"' || ch === "'") {
      quote = ch;
      out += ch;
      continue;
    }
    if (ch === '#' && (i === 0 || /\s/.test(text[i - 1]))) break;
    out += ch;
  }
  return out.replace(/\s+$/, '');
}

function parseScalar(raw) {
  const text = String(raw).trim();
  if (text === '') return null;
  if ((text.startsWith('"') && text.endsWith('"') && text.length > 1) || (text.startsWith("'") && text.endsWith("'") && text.length > 1)) {
    return text.slice(1, -1).replace(/\\"/g, '"');
  }
  if (text === 'true') return true;
  if (text === 'false') return false;
  if (text === 'null' || text === '~') return null;
  if (/^-?\d+$/.test(text)) return Number(text);
  if (/^-?\d*\.\d+$/.test(text)) return Number(text);
  return text;
}

function splitFlow(inner) {
  const parts = [];
  let buf = '';
  let quote = null;
  let depth = 0;
  for (const ch of inner) {
    if (quote) {
      buf += ch;
      if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'") {
      quote = ch;
      buf += ch;
      continue;
    }
    if (ch === '[' || ch === '{') depth++;
    if (ch === ']' || ch === '}') depth--;
    if (ch === ',' && depth === 0) {
      parts.push(buf);
      buf = '';
      continue;
    }
    buf += ch;
  }
  if (buf.trim() !== '') parts.push(buf);
  return parts.map(parseScalar).filter((v) => v !== null);
}

/**
 * Parse a region of RAW (not yet comment-stripped) lines at a given indent into a value.
 * Returns { value, next } where `next` is the first unconsumed line index.
 *
 * Comment stripping happens here, one line at a time, and only on the lines being read as
 * YAML *structure*. It never touches the inside of a block scalar, because a block scalar
 * is literal by definition: a `#` in there is a character of the value, not a comment. That
 * distinction is load-bearing for `enumerate:`, which holds commands an agent copies and
 * runs — `rg "#[0-9a-f]{6}" src/`, `git log --format='%h # %s'`, a shell comment on an
 * example line. Stripping those truncated the line silently and told nobody.
 */
function parseRegion(lines, start, end, indent) {
  // Structure is read comment-stripped; block-scalar content is read raw, below.
  const yaml = (n) => stripComment(lines[n]);

  // block sequence?
  let i = start;
  while (i < end && yaml(i).trim() === '') i++;
  if (i >= end) return { value: null, next: end };

  if (yaml(i).trim().startsWith('- ') || yaml(i).trim() === '-') {
    const arr = [];
    while (i < end) {
      const line = yaml(i);
      if (line.trim() === '') {
        i++;
        continue;
      }
      if (indentOf(line) < indent) break;
      const t = line.trim();
      if (!t.startsWith('-')) break;
      arr.push(parseScalar(t.replace(/^-\s*/, '')));
      i++;
    }
    return { value: arr, next: i };
  }

  const map = {};
  while (i < end) {
    const line = yaml(i);
    if (line.trim() === '') {
      i++;
      continue;
    }
    const ind = indentOf(line);
    if (ind < indent) break;
    const t = line.trim();
    const m = /^([^:]+):(.*)$/.exec(t);
    if (!m) {
      throw userError(`lens front matter: cannot parse line ${i + 1} — "${t}"`);
    }
    const key = parseScalar(m[1]) ?? m[1].trim();
    const rest = m[2].trim();
    i++;

    if (rest === '|' || rest === '>' || rest === '|-' || rest === '>-') {
      const folded = rest.startsWith('>');
      const block = [];
      let blockIndent = null;
      while (i < end) {
        // Raw, deliberately. Everything from here to the dedent is the value.
        const bl = lines[i];
        if (bl.trim() === '') {
          block.push('');
          i++;
          continue;
        }
        const bi = indentOf(bl);
        if (bi <= ind) break;
        if (blockIndent === null) blockIndent = bi;
        block.push(bl.slice(Math.min(bi, blockIndent)));
        i++;
      }
      while (block.length && block[block.length - 1] === '') block.pop();
      map[String(key)] = folded ? block.join(' ').replace(/\s+/g, ' ').trim() : block.join('\n');
      continue;
    }

    if (rest.startsWith('[')) {
      let buf = rest;
      let depth = (buf.match(/\[/g) || []).length - (buf.match(/\]/g) || []).length;
      while (depth > 0 && i < end) {
        const cont = yaml(i);
        buf += ' ' + cont.trim();
        depth += (cont.match(/\[/g) || []).length - (cont.match(/\]/g) || []).length;
        i++;
      }
      const inner = buf.slice(buf.indexOf('[') + 1, buf.lastIndexOf(']'));
      map[String(key)] = splitFlow(inner);
      continue;
    }

    if (rest === '') {
      // nested mapping or block sequence, if the next content line is deeper
      let j = i;
      while (j < end && yaml(j).trim() === '') j++;
      if (j < end && indentOf(yaml(j)) > ind) {
        const sub = parseRegion(lines, j, end, indentOf(yaml(j)));
        map[String(key)] = sub.value;
        i = sub.next;
      } else {
        map[String(key)] = null;
      }
      continue;
    }

    map[String(key)] = parseScalar(rest);
  }
  return { value: map, next: i };
}

/** Split `---` front matter from the body. Returns { data, body }. */
export function parseFrontMatter(text, { label = 'lens' } = {}) {
  const normalised = String(text).replace(/^﻿/, '').replace(/\r\n/g, '\n');
  const lines = normalised.split('\n');
  if (lines[0].trim() !== '---') {
    throw userError(`${label} has no YAML front matter — it must start with a "---" line.`);
  }
  let close = -1;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === '---') {
      close = i;
      break;
    }
  }
  if (close === -1) throw userError(`${label} front matter is never closed with a "---" line.`);
  // Raw lines. parseRegion strips comments per line as it reads structure, so a `#` inside
  // a block scalar stays the character the author typed.
  const fmLines = lines.slice(1, close);
  const { value } = parseRegion(fmLines, 0, fmLines.length, 0);
  // Where each top-level key was declared, 1-based in the file. A shape complaint that
  // cannot say which line to open is a complaint the author has to go hunting for; the file
  // is 25 KB of prose and the front matter is the first forty lines of it.
  //
  // Only column 0 is scanned, and only structure lives there: a block scalar's content is
  // always indented deeper than its key, and a key at indent 0 puts it at indent 1 or more.
  const lineOf = {};
  fmLines.forEach((raw, idx) => {
    if (indentOf(raw) !== 0) return;
    const m = /^([^:#\s][^:]*):/.exec(raw);
    if (!m) return;
    const key = m[1].trim();
    if (!(key in lineOf)) lineOf[key] = idx + 2; // +1 for the opening `---`, +1 for 1-based
  });
  return {
    data: value && typeof value === 'object' && !Array.isArray(value) ? value : {},
    body: lines.slice(close + 1).join('\n').replace(/^\n+/, ''),
    lineOf,
  };
}

// ---------------------------------------------------------------------------
// lens loading
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// shape validation
//
// A lens pack that half-loads is the worst outcome available here, and the `scale: |` bug
// is the proof: the block scalar parsed cleanly, every rung landed in one string, the
// mapping check rejected it, `scale` stayed `{}`, `ponder start` printed "scale —", and the
// session ran to convergence grading against a rubric that had no rungs. No error, no
// warning, and the file was still wrong the next time somebody used it.
//
// So the engine refuses instead of repairing. Repairing `scale: |` is tempting — the two
// lines under it obviously mean `1: broken` and `5: exemplary` — but it is guesswork the
// moment a rung's wording contains a colon ("3: acceptable: nothing chosen"), and `>` folds
// the whole block onto one line where there is nothing left to split on. Worse, a repair
// leaves the author believing the file is right, so the next field they get wrong gets no
// such rescue and the *next* lens ships broken too. A refusal that names the file, the line
// and the shape fixes the file once and teaches the shape. The cost of refusing is thirty
// seconds; the cost of guessing is a graded pass nobody can trust.
//
// Every field is checked, and every problem is reported at once, so one edit fixes the file
// rather than one edit per run.
// ---------------------------------------------------------------------------

const RUNGS = ['1', '2', '3', '4', '5'];

const SHAPE_EXAMPLE = [
  'a lens pack declares all five of these:',
  '',
  '  name: ui                       # one lowercase word',
  '  unit: screen                   # the singular noun for one gradable thing',
  '  enumerate: |                   # a block scalar: how to find every unit',
  '    1. List every route.',
  '    2. Add one unit per state each route can be in.',
  '  dimensions: [clarity, density, accessibility]   # a list, 5 to 12 of them',
  '  scale:                         # a mapping, all five rungs, 1 to 5',
  '    1: broken',
  '    2: bad',
  '    3: acceptable',
  '    4: good',
  '    5: exemplary',
];

/** What a parsed value turned out to be, in the words the author would recognise. */
function shapeOf(value) {
  if (value === null || value === undefined) return 'not declared';
  if (Array.isArray(value)) return value.length === 0 ? 'an empty list' : 'a list';
  if (typeof value === 'object') return 'a mapping';
  if (typeof value === 'string') {
    if (value.trim() === '') return 'empty';
    return value.includes('\n') ? 'a block scalar' : 'a single value';
  }
  return `a ${typeof value}`;
}

function checkLens(data, file, lineOf) {
  const problems = [];
  const say = (key, text) => problems.push({ key, text, at: lineOf && lineOf[key] ? `line ${lineOf[key]}` : '' });

  if (typeof data.unit !== 'string' || data.unit.trim() === '') {
    say('unit', `${shapeOf(data.unit)}. Every coverage message names the unit, and there is nothing to count without one. Give it the singular noun for one gradable thing.`);
  }

  if (typeof data.enumerate !== 'string' || data.enumerate.trim() === '') {
    say('enumerate', `${shapeOf(data.enumerate)}. Coverage is graded units divided by enumerated units, so a lens with no procedure for finding units cannot close its universe and can never reach coverage 1.0. Write it as a block scalar, one step per line.`);
  }

  if (typeof data.dimensions === 'string') {
    say('dimensions', `a single value, so the whole line was read as one dimension name. Write it as a flow sequence: dimensions: [${data.dimensions.split(/\s*,\s*/).filter(Boolean).join(', ') || 'clarity, density'}].`);
  } else if (!Array.isArray(data.dimensions) || data.dimensions.length === 0) {
    say('dimensions', `${shapeOf(data.dimensions)}. Appraise grades every unit against these, so there is nothing to grade against. Write them as a flow sequence: dimensions: [clarity, density, accessibility].`);
  } else if (data.dimensions.some((d) => typeof d !== 'string' || d.trim() === '')) {
    say('dimensions', 'holds an empty or non-text entry. Every dimension becomes the `dimension` field on a finding, so each one has to be a short lowercase slug.');
  }

  const scale = data.scale;
  if (typeof scale === 'string' && scale.includes('\n')) {
    say('scale', 'a block scalar. The `|` made every rung one run of text, so the lens loaded with no scale at all and `ponder start` printed "scale —". Drop the `|` and let each rung be its own key.');
  } else if (!scale || typeof scale !== 'object' || Array.isArray(scale)) {
    say('scale', `${shapeOf(scale)}. The 1-to-5 rungs are the whole grading contract — a lens without them cannot be graded against. Write it as a mapping from rung to wording.`);
  } else {
    const keys = Object.keys(scale);
    const missing = RUNGS.filter((r) => !keys.includes(r));
    const extra = keys.filter((k) => !RUNGS.includes(k));
    const blank = RUNGS.filter((r) => keys.includes(r) && String(scale[r] ?? '').trim() === '');
    if (missing.length) say('scale', `no wording for rung ${missing.join(', ')}. SPEC 7 fixes the range at 1 to 5 and every rung has to be named, or a grader has to invent the ones you left out.`);
    if (extra.length) say('scale', `names rung ${extra.join(', ')}, which is outside the range. The scale runs 1 to 5 and nothing else.`);
    if (blank.length) say('scale', `rung ${blank.join(', ')} has no wording. A blank rung is a rung a grader will not use.`);
  }

  if (problems.length === 0) return;
  // The detail lines are printed under a two-space indent, and each problem hangs under an
  // eight-column "line NN" gutter, so the text itself gets cols - 10.
  const GUTTER = 8;
  const cols = termCols(process.stderr);
  const detail = [];
  for (const p of problems) {
    // prose: these sentences quote flags, pipes and `|` on purpose, and the command-shape
    // test would read every one of them as a command and refuse to wrap it.
    const lines = wrap(`${p.key}: ${p.text}`, { cols: cols - 2 - GUTTER, prose: true }).split('\n');
    detail.push(p.at.padEnd(GUTTER) + lines[0]);
    for (const l of lines.slice(1)) detail.push(' '.repeat(GUTTER) + l);
  }
  detail.push('');
  detail.push(...SHAPE_EXAMPLE);
  throw userError(
    `${file} is not a usable lens pack — ${problems.length === 1 ? 'one field is' : `${problems.length} fields are`} the wrong shape.`,
    detail,
  );
}

function shapeLens(data, body, file, requestedName, lineOf) {
  checkLens(data, file, lineOf);
  const name = typeof data.name === 'string' && data.name.trim() !== '' ? data.name.trim() : requestedName;
  const scale = {};
  for (const [k, v] of Object.entries(data.scale)) scale[String(k)] = v === null ? '' : String(v);
  return {
    name,
    unit: data.unit.trim(),
    dimensions: data.dimensions.map((d) => String(d).trim()),
    scale,
    enumerate: data.enumerate.trim(),
    front: data,
    body,
    path: file,
  };
}

/** Load a lens by name, or a custom rubric file. Throws a userError the agent can act on. */
export function loadLens(name, { rubric = null } = {}) {
  if (!name || typeof name !== 'string') {
    throw userError('a lens is required:  --lens <name>', [`installed: ${availableLenses().join(', ') || 'none'}`]);
  }
  let file;
  if (name === 'custom') {
    if (!rubric) {
      throw userError('--lens custom needs --rubric <file> pointing at a lens pack with the same front-matter shape.');
    }
    file = path.resolve(rubric);
  } else if (rubric) {
    file = path.resolve(rubric);
  } else {
    file = path.join(lensDir(), `${name}.md`);
  }
  let text;
  try {
    text = fs.readFileSync(file, 'utf8');
  } catch (err) {
    if (err.code === 'ENOENT') {
      const installed = availableLenses();
      throw userError(`no lens pack at ${file}.`, [
        installed.length ? `installed lenses: ${installed.join(', ')}` : `no lens packs found in ${lensDir()}`,
        'or supply your own:  --lens custom --rubric <file>',
      ]);
    }
    throw userError(`cannot read lens pack ${file}: ${err.code || err.message}`);
  }
  const { data, body, lineOf } = parseFrontMatter(text, { label: `lens pack ${file}` });
  return shapeLens(data, body, file, name, lineOf);
}

/** One-line description used by start, status and doctor. */
export function lensSummary(lens) {
  if (!lens) return 'unknown lens';
  return `${lens.name} — unit = ${lens.unit}, ${lens.dimensions.length} dimensions`;
}

/** The scale rungs as "1 broken · 3 acceptable · 5 exemplary". */
export function scaleSummary(lens) {
  if (!lens || !lens.scale) return '';
  return Object.entries(lens.scale)
    .map(([k, v]) => `${k} ${v}`)
    .join(' · ');
}
