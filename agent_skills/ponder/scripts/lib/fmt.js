// Terminal output helpers for ponder.
//
// Colour is applied only when the destination is a real TTY and NO_COLOR is unset.
// FORCE_COLOR=1 turns it on regardless (used by the conformance suite when it wants to
// assert on styled output). Every helper returns a string; nothing here writes to stdout,
// so `--json` mode can build the same values without emitting them.

const SGR = {
  bold: ['\x1b[1m', '\x1b[22m'],
  dim: ['\x1b[2m', '\x1b[22m'],
  underline: ['\x1b[4m', '\x1b[24m'],
  red: ['\x1b[31m', '\x1b[39m'],
  green: ['\x1b[32m', '\x1b[39m'],
  yellow: ['\x1b[33m', '\x1b[39m'],
  blue: ['\x1b[34m', '\x1b[39m'],
  magenta: ['\x1b[35m', '\x1b[39m'],
  cyan: ['\x1b[36m', '\x1b[39m'],
  grey: ['\x1b[90m', '\x1b[39m'],
};

const ANSI_RE = /\x1b\[[0-9;]*m/g;

// Layout width. Narrower than 40 columns and a hanging indent leaves no room for the value;
// wider than 120 and prose stops being readable, so a maximised terminal gets a measure
// rather than a 300-column line. 88 is the width used when there is no terminal to ask.
const MIN_COLS = 40;
const MAX_COLS = 120;
const FIXED_COLS = 88;

const clampCols = (n) => Math.max(MIN_COLS, Math.min(MAX_COLS, Math.trunc(n)));

/**
 * True when output is being laid out for a terminal at all.
 *
 * `--json` output must stay byte-stable, so nothing wraps in that mode. PONDER_NO_WRAP=1
 * is the same switch for a caller that is piping human output somewhere that re-flows it.
 */
export function wrapEnabled() {
  if (process.env.PONDER_NO_WRAP === '1') return false;
  return !process.argv.slice(2).includes('--json');
}

/**
 * The width to lay output out at.
 *
 * COLUMNS wins, because it is the shell's own answer and the only lever a non-TTY caller
 * has — the conformance suite and `COLUMNS=100 ponder start` both go through it. Then the
 * stream's own width when it is a real terminal. Off a terminal, a fixed width: output
 * captured into a file or a pipe still has to be readable, and 0 or Infinity columns is not
 * a width, it is an unwrapped line.
 */
export function termCols(stream = process.stdout) {
  const env = Number(process.env.COLUMNS);
  if (Number.isFinite(env) && env > 0) return clampCols(env);
  if (stream && stream.isTTY && Number.isFinite(stream.columns) && stream.columns > 0) {
    return clampCols(stream.columns);
  }
  return FIXED_COLS;
}

/** True when ANSI colour should be emitted for `stream`. */
export function colorEnabled(stream = process.stdout) {
  // NO_COLOR wins over everything, per the no-color.org convention.
  const no = process.env.NO_COLOR;
  if (typeof no === 'string' && no !== '') return false;
  const force = process.env.FORCE_COLOR;
  if (force !== undefined && force !== '' && force !== '0') return true;
  return Boolean(stream && stream.isTTY);
}

function paint(name, text, stream) {
  if (text === null || text === undefined) text = '';
  text = String(text);
  if (!colorEnabled(stream)) return text;
  const [on, off] = SGR[name];
  return on + text + off;
}

/** Colour functions. Each degrades to identity when colour is off. */
export const c = Object.fromEntries(
  Object.keys(SGR).map((name) => [name, (text, stream) => paint(name, text, stream)]),
);

/** Visible width of a string, ignoring ANSI escapes. */
export function width(s) {
  return String(s ?? '').replace(ANSI_RE, '').length;
}

export function strip(s) {
  return String(s ?? '').replace(ANSI_RE, '');
}

function padEnd(s, n) {
  const pad = n - width(s);
  return pad > 0 ? s + ' '.repeat(pad) : s;
}

function padStart(s, n) {
  const pad = n - width(s);
  return pad > 0 ? ' '.repeat(pad) + s : s;
}

/** A bold section heading with a blank line before it. */
export function head(title) {
  return c.bold(title);
}

/**
 * Lay one kv value out as the lines that go to the right of the key.
 *
 * A kv value is a value, not a document: whatever line breaks reached it came from a caller
 * guessing at a width, and this function knows the real one. So consecutive lines are
 * re-flowed into one paragraph and wrapped to `avail`; only a blank line survives, because
 * losing it loses meaning rather than layout.
 *
 * Prose, deliberately. A kv row is a label and a value — the commands live in the enumerate
 * block, which goes through `wrap` directly. Running the command-shape test here made one
 * apostrophe enough to freeze a whole row: the product lens's scale ends on the word
 * `user's`, and that one `'` printed all 264 characters of the row on a single line.
 */
function valueLines(value, avail) {
  const out = [];
  let para = [];
  const flush = () => {
    if (para.length === 0) return;
    for (const line of wrap(para.join(' '), { cols: avail, prose: true }).split('\n')) out.push(line);
    para = [];
  };
  for (const raw of String(value ?? '').split('\n')) {
    if (raw.trim() === '') {
      flush();
      out.push('');
      continue;
    }
    para.push(raw.trim());
  }
  flush();
  return out.length ? out : [''];
}

/**
 * Two-column aligned key/value block.
 * pairs: [[key, value], ...]  — a null pair renders as a blank line.
 *
 * A value longer than the line wraps, and its continuations hang under the value column
 * rather than resetting to the left margin, so a wrapped row still reads as one row. This
 * is not cosmetic: `ponder start` prints the lens scale here, and the scale is the whole
 * grading contract — laid out as one 204-character line it is the row an agent skims past.
 *
 * A value the caller has already broken into lines is re-flowed and re-hung under the value
 * column, so a caller never has to know the key width to line a multi-line value up, and one
 * that used to hard-code the alignment still lands in exactly the right place.
 *
 * A long unbroken token — a path, a DSN — overflows rather than being cut in half. A broken
 * path is worse than a long one.
 */
export function kv(pairs, { indent = 2, gap = 2, cols = null } = {}) {
  const rows = pairs.filter((p) => Array.isArray(p));
  const keyWidth = rows.reduce((m, [k]) => Math.max(m, width(k)), 0);
  const valueCol = indent + keyWidth + gap;
  const hang = ' '.repeat(valueCol);
  const limit = cols === null ? termCols() : cols;
  const avail = Math.max(20, limit - valueCol);
  const out = [];
  for (const p of pairs) {
    if (!Array.isArray(p)) {
      out.push('');
      continue;
    }
    const [k, v] = p;
    const lines = valueLines(v, avail);
    const lead = ' '.repeat(indent) + padEnd(c.grey(k), keyWidth) + ' '.repeat(gap);
    out.push((lead + (lines[0] ?? '')).replace(/[ \t]+$/, ''));
    for (let i = 1; i < lines.length; i++) out.push((hang + lines[i]).replace(/[ \t]+$/, ''));
  }
  return out.join('\n');
}

/**
 * A simple aligned table. `align` is a per-column 'l' | 'r' string.
 * Rows are stringified as-is, so callers may pre-colour cells.
 */
export function table(headers, rows, { indent = 2, gap = 2, align = '' } = {}) {
  const all = [headers, ...rows];
  const cols = headers.length;
  const widths = [];
  for (let i = 0; i < cols; i++) {
    widths[i] = all.reduce((m, r) => Math.max(m, width(r[i] ?? '')), 0);
  }
  const line = (cells, styler) =>
    ' '.repeat(indent) +
    cells
      .map((cell, i) => {
        const text = styler ? styler(String(cell ?? '')) : String(cell ?? '');
        const a = align[i] === 'r' ? padStart : padEnd;
        return i === cols - 1 && align[i] !== 'r' ? text : a(text, widths[i]);
      })
      .join(' '.repeat(gap))
      .replace(/\s+$/, '');
  const out = [line(headers, (s) => c.grey(s))];
  for (const r of rows) out.push(line(r));
  return out.join('\n');
}

export function bullet(text, { indent = 2, mark = '-' } = {}) {
  return `${' '.repeat(indent)}${mark} ${text}`;
}

export function warn(text) {
  return `${c.yellow('warning')} ${text}`;
}

export function problem(text) {
  return `${c.red('error')} ${text}`;
}

export function ok(text) {
  return `${c.green('ok')} ${text}`;
}

/**
 * Marks that a line is a command, not prose, and must reach the terminal byte for byte.
 *
 * A lens pack's `enumerate:` block is the clearest case: it holds commands an agent is
 * meant to copy and run, and a wrapped command is a broken command. Re-flowing also
 * collapses runs of whitespace, which silently rewrites a format string (`--format='%h  %s'`
 * loses a column) and flattens an awk program.
 *
 * The three ways to handle a long command are: never wrap the block, wrap only its prose,
 * or wrap with a `\` continuation. The third is wrong — inside single quotes a backslash is
 * a literal character, so breaking `rg '#[0-9a-f]{6}'` that way corrupts the pattern rather
 * than continuing it, and the trick is shell-specific besides. The first throws away the
 * wrapping that keeps the block's explanatory prose readable at terminal width. So: wrap
 * prose, pass commands through untouched.
 *
 * The test is deliberately eager. A false positive costs one long line that a terminal soft
 * wraps anyway; a false negative hands the agent a command that does not run.
 */
const COMMAND_SHAPE = [
  /['"`]/, //                       a quoted run — whitespace inside it is content
  /\\$/, //                         a trailing backslash — this command continues below
  /\$[({A-Za-z_]/, //               $VAR, ${VAR}, $(sub)
  /(?:^|\s)(?:\|\||&&|[|;])/, //    pipes and command chaining
  /(?:^|\s)\d?[<>]/, //             redirects, 2> included
  /(?:^|\s)--?[A-Za-z0-9]/, //      a command-line flag
  /(?:^|\s)#/, //                   a hex colour, a shell comment, a markdown heading
];

const isCommandShaped = (line) => COMMAND_SHAPE.some((re) => re.test(line));

/**
 * Wrap prose to `cols`, preserving existing newlines. `cols` defaults to the terminal's
 * width, so COLUMNS and a resized window both reach the output.
 *
 * Five things are preserved that a naive re-flow destroys: command lines (above), the
 * leading indentation of every line — a continuation line in an `enumerate:` block is
 * indented under the command it continues, and printing it flush left turns a two-line
 * command into two commands, the second of which is not a command — the runs of whitespace
 * inside a line (wrapping inserts line breaks, it does not get to rewrite the spacing an
 * author chose), the alignment of a wrapped list item, whose continuations hang under the
 * text rather than under the marker so that one long step still reads as one step and not
 * three, and the width of a coloured string, which is measured without its ANSI escapes so
 * that a styled value does not wrap ten columns early.
 *
 * `prose: true` turns off the command-shape test for a caller that knows its text is prose.
 * The test is deliberately eager, and an English sentence that quotes a flag or a `|` reads
 * as a command to it; a caller writing its own error text does not have to phrase around
 * that.
 */
export function wrap(text, { cols = null, indent = 0, prose = false } = {}) {
  const s = String(text ?? '');
  const pad = ' '.repeat(indent);
  if (!wrapEnabled()) {
    return s
      .split('\n')
      .map((l) => (l.trim() === '' ? '' : pad + l.replace(/\s+$/, '')))
      .join('\n');
  }
  const limit = (cols === null ? termCols() : cols) - indent;
  const out = [];
  let continued = false; // the previous line ended with a shell `\`
  for (const raw of s.split('\n')) {
    if (raw.trim() === '') {
      out.push('');
      continued = false;
      continue;
    }
    const line = raw.replace(/\s+$/, '');
    if (!prose && (continued || isCommandShaped(line))) {
      out.push(pad + line);
      continued = /\\$/.test(line);
      continue;
    }
    continued = false;
    const lead = /^[ \t]*/.exec(line)[0];
    const body = line.slice(lead.length);
    const marker = /^(?:\d+[.)]|[-*+•])\s+/.exec(body);
    const hang = lead + ' '.repeat(marker ? marker[0].length : 0);
    // Split keeping the separators, so a break drops exactly one run of whitespace and
    // every other run reaches the terminal as the author typed it.
    const parts = body.split(/([ \t]+)/);
    let cur = lead + parts[0];
    for (let k = 1; k < parts.length; k += 2) {
      const sep = parts[k];
      const word = parts[k + 1] ?? '';
      if (width(cur) + sep.length + width(word) <= limit) cur += sep + word;
      else {
        out.push(pad + cur);
        cur = hang + word;
      }
    }
    if (cur.trim() !== '') out.push(pad + cur);
  }
  return out.join('\n');
}

/**
 * The line that survives context compaction.
 * Always the last line of human output, always naming the phase AND the concrete command.
 */
export function nextLine(phase, command) {
  return `${c.bold('NEXT:')} ${c.cyan(phase)} — ${command}`;
}

/** Format a 0-1 ratio as a fixed-width decimal. `null` renders as an em dash. */
export function num(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return Number(value).toFixed(digits);
}

export function pct(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return `${(Number(value) * 100).toFixed(digits)}%`;
}

/** Colour a metric by whether it is inside its healthy band. */
export function signal(value, { good, bad, invert = false } = {}) {
  const s = num(value);
  if (value === null || value === undefined) return s;
  const v = Number(value);
  const isBad = invert ? v < bad : v > bad;
  const isGood = invert ? v >= good : v <= good;
  if (isBad) return c.red(s);
  if (isGood) return c.green(s);
  return c.yellow(s);
}

const VERDICT_COLOR = {
  continue: 'blue',
  stop: 'green',
  escalate: 'yellow',
  blocked: 'red',
};

export function verdictLabel(verdict) {
  const fn = c[VERDICT_COLOR[verdict] ?? 'bold'];
  return fn(c.bold(verdict ?? '—'));
}

const STATUS_COLOR = {
  open: 'blue',
  converged: 'green',
  stopped: 'yellow',
  aborted: 'red',
  applied: 'magenta',
};

export function statusLabel(status) {
  const fn = c[STATUS_COLOR[status] ?? 'bold'];
  return fn(status ?? '—');
}

/**
 * Truncate to `n` visible characters with an ellipsis.
 * Counts code points, not UTF-16 units, so clipping a subject like "the ✨ UI" cannot cut an
 * emoji in half and leave a lone surrogate in the output.
 */
export function clip(text, n) {
  const s = String(text ?? '');
  const chars = [...s];
  return chars.length <= n ? s : chars.slice(0, Math.max(0, n - 1)).join('') + '…';
}

/** Right-pad a list of ids into a readable, wrapped, comma-joined block. */
export function idList(ids, { cols = null, indent = 4 } = {}) {
  if (!ids || ids.length === 0) return '';
  return wrap(ids.join(', '), { cols: cols === null ? termCols() : cols, indent });
}
