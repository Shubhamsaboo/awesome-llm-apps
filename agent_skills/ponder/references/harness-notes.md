# Harness notes - Claude Code, Codex, and OpenClaw

This skill is one directory, symlinked into every agent harness (`~/.claude/skills/ponder`,
`~/.agents/skills/ponder`, and `~/.codex/skills/ponder`). Everything here is the set of
differences that actually change what you type.

## Install

One source of truth, symlinked everywhere:

```sh
git clone https://github.com/Quinnod345/ponder.git ~/code/ponder
~/code/ponder/install.sh
```

It links `skill/ponder` into `~/.claude/skills/ponder`, `~/.agents/skills/ponder` (and
`~/.codex/skills/ponder` when `~/.codex` exists) and `bin/ponder` into `~/.local/bin`, then runs
`ponder doctor`. Re-running is safe - it replaces its own symlinks and refuses to clobber a real
directory. The equivalent by hand:

```sh
ln -s ~/code/ponder/skill/ponder ~/.claude/skills/ponder
ln -s ~/code/ponder/skill/ponder ~/.agents/skills/ponder
chmod +x ~/code/ponder/bin/ponder
ln -s ~/code/ponder/bin/ponder ~/.local/bin/ponder
```

`bin/ponder` is a POSIX `sh` shim, not JavaScript. That is deliberate: an extensionless JS file trips
Node's module resolution. It walks its own symlink chain before `exec node …/lib/cli.js "$@"`, because
without that a `ponder` symlinked onto PATH would look for `~/.local/lib/cli.js`. Do not "fix" either
part.

### Front matter

Only two keys, because only two keys are valid in both harnesses:

```yaml
---
name: ponder
description: …
---
```

Codex additionally understands an optional `metadata:` block - `disable-model-invocation`
(`~/.codex/skills/zoom-out/SKILL.md`), `argument-hint` (`~/.codex/skills/handoff/SKILL.md`) and
`short-description` (`~/.codex/vendor_imports/skills/skills/.curated/linear/SKILL.md`). Claude Code
reads the same keys at the top level instead, not nested - compare its own copy of zoom-out, which
carries a bare `disable-model-invocation: true`. So a `metadata:` block would make the two installs
behave differently from one file, and this skill has none.

The other rule the front matter has to obey is YAML's, and it bites in exactly one place: a plain
scalar cannot contain `: ` (colon-space). The `description` is a long prose line full of quoted
trigger phrases, and one stray colon-space in it makes the whole block unparseable - which in both
harnesses means the skill silently does not load rather than erroring. After any edit to it:

```sh
python3 -c "import yaml,sys; d=yaml.safe_load(open(sys.argv[1]).read().split('---',2)[1]); \
  assert set(d) == {'name','description'}, d.keys(); print('ok:', d['name'], len(d['description']))" \
  ~/code/ponder/skill/ponder/SKILL.md
```

### Checking the install

```sh
ls -l ~/.claude/skills/ponder ~/.codex/skills/ponder    # both should point at ~/code/ponder/skill/ponder
head -4 ~/.claude/skills/ponder/SKILL.md                 # front matter intact through the symlink
ponder doctor                                            # engine reachable, and what it can see
```

In **Claude Code**, the skill then appears in the available-skills list; `/ponder` invokes it, as does
the Skill tool with `skill: "ponder"`. In **Codex**, skills under `$CODEX_HOME/skills` (default
`~/.codex/skills`) are picked up on the **next turn** after installation, not the current one - if it
does not fire immediately, that is why.

## Invocation

Both harnesses model-invoke skills from the `description`, and both take an explicit `/ponder`. The
practical difference: Claude Code surfaces the skill list to the model every turn, so a trigger
phrase reliably fires mid-conversation. In Codex, a skill invoked deep in a long session sometimes
needs the explicit `/ponder` - if the user says "keep pondering" and nothing loads, read the SKILL.md
by path and carry on rather than debating it:

```sh
cat ~/code/ponder/skill/ponder/SKILL.md
```

## Subagents and fan-out

| | Claude Code | Codex |
|---|---|---|
| In-process subagents | **Agent tool.** Multiple calls in one message run in parallel. Returns text to the parent. | None. |
| Very large sweeps | **Workflow tool** - handles batching, retries and collection better than hand-rolled parallel agents. | None. |
| Subprocess agents | possible, rarely worth it | **`codex exec`** - the primary mechanism |
| Background | Bash tool `run_in_background`, plus Monitor to wait on a condition | `&` + `wait`, or `nohup … &` and poll the output file |

`codex exec` flags that matter for fan-out:

```sh
codex exec -C "$PWD" \
  --sandbox workspace-write \
  --skip-git-repo-check \
  -o .ponder/tmp/batch-3.txt \
  "…prompt…"
```

- `-C, --cd <DIR>` - working root for the child.
- `-s, --sandbox read-only|workspace-write|danger-full-access` - the child's own sandbox, independent
  of yours.
- `--add-dir <DIR>` - extra writable directory, needed if the session state lives outside the workspace.
- `-o, --output-last-message <FILE>` - writes the child's final message to a file. **This is what makes
  fan-out collectible.** Have the child write its JSONL to disk anyway and return only the path plus a
  count; then `-o` is your receipt, not your payload.
- `--output-schema <FILE>` - a JSON Schema for the final response, when you want the shape enforced.
- `--json` - event stream as JSONL on stdout, for progress monitoring.
- `--ephemeral` - no session files on disk, for throwaway batches.

Two of those are load-bearing rather than optional, and both were checked on this machine against
codex-cli 0.147.0:

- **`--skip-git-repo-check` is not paranoia.** Without it the child refuses before doing any work -
  `Not inside a trusted directory and --skip-git-repo-check was not specified`, exit `1`. Fan out over
  a subject that is not a git checkout and every batch dies at once, identically and instantly, which
  reads like a prompt problem and is not one.
- **`codex exec` reads stdin even when the prompt is an argument** (`Reading additional input from
  stdin...`). Backgrounded with `&` it inherits the parent's stdin, so redirect it: `… </dev/null &`.
  From `/dev/null` it takes the EOF and carries on; from a pipe nobody closes it does not.

`codex exec` starts a **fresh session**. It inherits none of your context, and it loads its own
`AGENTS.md` chain from `-C`. Everything the batch needs goes in the prompt or in a file it can read.

## The session lock

**The engine locks. Do not architect around a lost-update race - there isn't one.** Earlier revisions
of this file said the opposite and told you to defend against a hazard that does not exist. Here is
what actually happens, read out of `lib/session.js` and reproduced on this machine.

`lockSession()` takes an exclusive lock on the session directory before any command that writes
state: `units`, `predict`, `grade`, `deliberate`, `delta`, `judge`, `decide`, `apply`, `abort`, and
`verify --repair`. The read-only commands - `status`, `report`, `list`, `doctor`, and a plain
`verify` - take no lock, so you can always ask where a session is even while a pass is being written
into it. `verify` is the only command whose locking depends on a flag, for the obvious reason: with
`--repair` it rewrites the state files, without it it writes nothing at all.

| | |
|---|---|
| Mechanism | `open(.ponder/<slug>/.lock, 'wx')` - atomic create-exclusive. The winner writes its pid and a timestamp into the file; the file's *existence* is the lock |
| Contending command | polls every 60 ms (`Atomics.wait`, no CPU spin) for up to **10 seconds** |
| Wait exhausted | exits **`1`**: `another ponder command is already working on <slug>.` - and names the lock file |
| Stale reclaim | a `.lock` whose mtime is older than **120 seconds** is deleted and taken. This is what covers a `kill -9` |
| Normal release | `unlink` when the command finishes, plus a process `exit` hook for `process.exit()` |
| Unlockable store | if the lock cannot be created for any reason other than `EEXIST`, the command runs without one. A safety net must not become a new way to fail |

**What the loser of a real race sees.** Two `ponder delta` calls fired at the same pass, measured:

```
A rc=2   error out of order: "ponder delta" satisfies revise, but this session owes judge.
B rc=0   ponder delta - pass 1, 1 delta applied
```

The lock serialises them and the phase machine finishes the job. B takes the lock, applies its batch,
and advances the phase from `revise` to `judge`. A waits a few milliseconds, takes the lock, reloads
`session.json` from disk - and now owes `judge`, so its `ponder delta` is out of order and exits `2`
without applying anything. The ledger grew by exactly one line, `findings.json` agrees with it, and
the phase advanced exactly once. Two `ponder decide` at once record one pass, not two. Two
`ponder start` on one slug: `mkdir` without `recursive` is the atomic claim, so the second exits `1`
with `session "<slug>" already exists`.

The conformance suite pins this: **45 checks** in `concurrency: racing deltas have exactly one winner`
and 14 more in `concurrency: racing decisions and starts have one winner too`, run over three fresh
sessions because a lock-free engine only loses the race some of the time. Making `lockSession` a
no-op fails both.

**What this means for fan-out.** The rule is unchanged - *only the parent runs `ponder`* - but the
reason is sequencing, not corruption. A race has a winner and a loser, and **the loser's work is
refused, not merged**. A subagent that calls `ponder delta` and does not check its exit code will
report success while its entire batch went nowhere. So: batch agents write JSONL to disk and return a
path plus a count, the parent concatenates, and the parent makes one call. That also keeps `f-NNNN`
assignment and the ledger in one place, which is where they belong.

Two practical notes. The 10-second wait is generous against a command that finishes in well under a
second, but a command stuck on a slow OCA bridge call (5 s per call) can outlast it - if a queued
command exits `1` on the lock, re-run it rather than deleting the file. And delete a `.lock` by hand
only when you know the process that made it is gone; otherwise wait, or let the 120-second stale
reclaim do it for you.

## Sandboxing, and whether psql is reachable

**Claude Code on this machine:** the Bash tool is sandboxed, and the sandbox does not block the OCA.
Verified: `psql "postgres://localhost/oneiro" -tAc "select 1"` returns `1` from inside the tool. Writes
into the project tree are fine. If a bridge call ever does get blocked, ponder degrades silently by
design - check `.ponder/<slug>/oca.log`, not the engine.

**Codex on this machine:** `~/.codex/config.toml` sets `sandbox_mode = "danger-full-access"` and
`approval_policy = "never"`, so psql works and state can be written anywhere.

**Codex under any other policy - including any `codex exec -s workspace-write` you spawn yourself.**
The three below follow from Codex's documented sandbox semantics and were **not** reproduced on this
machine, because the config above makes the failure path unreachable here. Treat them as what to
expect, and check with `ponder doctor` rather than assuming:

- **Network is off under `workspace-write` by default.** `psql` to `postgres://localhost/oneiro` over
  TCP should fail. The bridge returns `null`, the loop runs identically, and you lose prior-pondering
  recall and the OCA writes. That is the designed degradation, not a bug - but do not promise the user
  cross-session memory from a run you made in that sandbox.
- **Writes outside the workspace are blocked.** The `~/.ponder/<slug>/` fallback should fail. Keep the
  session inside the project with `ponder start --project "$PWD"`, or widen the child's sandbox when
  you spawn it - `codex exec --add-dir ~/.ponder`. `--add-dir` is a **`codex exec`** flag, not a
  ponder one; `ponder start --add-dir` exits `1` with `unknown flag --add-dir`.
- **`read-only` cannot run a pass at all** - every command in the loop writes state. The
  inspection commands that write nothing (`status`, `list`, `verify` without `--repair`) should
  still work, which is enough to find out where a session stands but not to move it.

`ponder doctor` settles all three in one call: it prints whether the OCA is reachable and which
store roots are writable. Run it inside the child sandbox, not outside it.

Rule of thumb: run `ponder doctor` as the first command in any unfamiliar harness. It reports node,
psql, the DSN, OCA reachability and where state will be written, which is exactly the set of things
that differ between these two environments.

## Context and compaction

Claude Code compacts long sessions, and a compaction is the single most likely way a long ponder
dies. Codex has no compaction guarantee and a smaller effective working window in practice. The
mitigation is the same in both and it is already built in: state lives in files, and every command
prints `NEXT:`. After any loss, `ponder status` tells you what you owe; `.ponder/<slug>/ledger.jsonl`
tells you everything every pass did and why.

Practical consequence for Codex specifically: prefer sequential batches that write JSONL to disk and
drop the detail, over holding 40 units' worth of code in one context. The disk is the memory.

## Paths

Skill-relative references (`references/protocol.md`) resolve differently per harness -
`~/.claude/skills/ponder/references/…` vs `~/.codex/skills/ponder/references/…`. Both are symlinks to
the same place, so when in doubt use the repo path, which is always correct:

```sh
~/code/ponder/skill/ponder/references/protocol.md
~/code/ponder/lenses/ui.md
```

Session state goes in `<project>/.ponder/`. It is plain JSON and JSONL. Commit it when the ledger is
worth keeping across branches and machines - that history is the point of the append-only design -
otherwise add `.ponder/` to `.gitignore`. Do not commit `.ponder/tmp/`.

## Known bites

- **`codex exec` hangs with no output, including `--version`.** Seen on macOS when codex is
  launched over SSH or tmux: a macOS Gatekeeper/amfid block keyed to the install path. Run a
  clean-path copy of the binary instead.
- **A queued command that exits `1` on the lock.** Not corruption - the session lock did its job and
  the wait ran out. Re-run the command. See [The session lock](#the-session-lock); do not delete a
  `.lock` file unless the process that wrote it is gone.
- **A skill edit that does not take effect.** Both harnesses read SKILL.md at load; edit the repo copy
  (`~/code/ponder/skill/ponder/SKILL.md`) and start a new turn - in Codex, a new session.
- **The OCA's cognitive-loop process on `:3333` is not running.** Nothing in ponder depends on it; the
  bridge shells out to `psql` directly. If something suggests otherwise, it is wrong.
