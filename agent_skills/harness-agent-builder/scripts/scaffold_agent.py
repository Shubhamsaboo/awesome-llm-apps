#!/usr/bin/env python3
"""Scaffold a production agent on the iii engine's harness worker.

Generates one Node file of business logic (plus package.json) that plugs
into the reusable workers on the engine bus: harness (turn loop), llm-router
(models), session-manager (transcripts), iii-state (storage), web (fetch),
and the cron / http trigger types. The generated code follows the consumer
contract: harness::send starts a turn, a harness::turn-completed binding
receives the result, and the model id always comes from router::models::list
or an explicit override, never a hardcoded default.

Offline and deterministic: writes files from templates, no network, no
timestamps, no randomness. Python 3.8+, stdlib only.
"""

import argparse
import json
import os
import re
import sys

VALID_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
VALID_FUNCTION = re.compile(r"^[a-z0-9_-]+(::[a-z0-9_*-]+)+$|^\*$")
CRON_FIELDS = 6


def fail(msg):
    print("error: %s" % msg, file=sys.stderr)
    return 2


def js_string(value):
    return json.dumps(value)


def render_agent(opts):
    ns = opts.name
    env_prefix = ns.upper()
    allow = list(opts.allow)
    lines = []
    w = lines.append

    w("import { registerWorker } from 'iii-sdk'")
    w("")
    w("const ENGINE_URL = process.env.III_URL || 'ws://localhost:49134'")
    w("const TIMEOUT_MS = Number(process.env.%s_TIMEOUT_MS || 5 * 60 * 1000)" % env_prefix)
    w("")
    if opts.output == "json":
        w("const OUTPUT_SCHEMA = {")
        w("  type: 'object',")
        w("  required: ['summary'],")
        w("  properties: {")
        w("    summary: { type: 'string' },")
        w("  },")
        w("}")
        w("")
    w("const SYSTEM_PROMPT = %s" % js_string(opts.prompt))
    w("")
    w("const iii = registerWorker(ENGINE_URL)")
    w("const waiters = new Map()")
    w("")
    w("iii.registerFunction(")
    w("  '%s::run'," % ns)
    w("  async (input) => {")
    w("    const task = typeof input === 'string' ? input : input?.task || input?.body?.task")
    w("    if (!task) throw new Error('%s::run requires { task: string }')" % ns)
    w("    return runTurn(task, input?.model)")
    w("  },")
    w("  {")
    w("    description: %s," % js_string(
        "Run the %s agent once: sends the task to the harness and returns the finished result." % ns))
    w("    request_format: {")
    w("      type: 'object',")
    w("      body: {")
    w("        task: { type: 'string' },")
    w("        model: { type: 'string', description: 'Model id from router::models::list' },")
    w("      },")
    w("    },")
    w("  },")
    w(")")
    w("")
    w("iii.registerFunction('%s::on-turn-completed', async (event) => {" % ns)
    w("  const waiter = waiters.get(event?.session_id)")
    w("  if (!waiter) return {}")
    w("  waiters.delete(event.session_id)")
    w("  clearTimeout(waiter.timer)")
    w("  if (event.status === 'completed' && event.result !== undefined) {")
    w("    waiter.resolve(event.result)")
    w("  } else {")
    w("    waiter.reject(new Error(`turn ${event.status}: ${event.result_error || event.reason || 'no result'}`))")
    w("  }")
    w("  return {}")
    w("})")
    w("")
    w("iii.registerTrigger({")
    w("  type: 'harness::turn-completed',")
    w("  function_id: '%s::on-turn-completed'," % ns)
    w("  config: {},")
    w("})")
    if opts.trigger == "cron":
        w("")
        w("iii.registerTrigger({")
        w("  type: 'cron',")
        w("  function_id: '%s::run'," % ns)
        w("  config: { expression: %s }," % js_string(opts.cron))
        w("})")
    w("")
    if opts.trigger == "http":
        w("async function bindHttpRoute() {")
        w("  try {")
        w("    await iii.trigger({")
        w("      function_id: 'engine::register_trigger',")
        w("      payload: {")
        w("        trigger_type: 'http',")
        w("        function_id: '%s::run'," % ns)
        w("        config: { api_path: %s, http_method: 'POST' }," % js_string("/" + ns))
        w("      },")
        w("    })")
        w("    console.error('[%s] REST route live: POST /%s')" % (ns, ns))
        w("  } catch {")
        w("    console.error('[%s] http worker not installed, REST route skipped (iii worker add http)')" % ns)
        w("  }")
        w("}")
        w("")
    w("async function resolveModel(requested) {")
    w("  if (requested) return requested")
    w("  if (process.env.%s_MODEL) return process.env.%s_MODEL" % (env_prefix, env_prefix))
    w("  const { models = [] } = await iii.trigger({ function_id: 'router::models::list', payload: {} })")
    w("  const usable = models.filter((m) => m.supports_tools).map((m) => m.id)")
    w("  if (usable.length === 1) return usable[0]")
    w("  if (usable.length === 0) {")
    w("    throw new Error('no models available: configure a provider in llm-router')")
    w("  }")
    w("  throw new Error(`several models available; set %s_MODEL to one of:\\n  ${usable.join('\\n  ')}`)" % env_prefix)
    w("}")
    w("")
    w("async function runTurn(task, requestedModel) {")
    w("  const model = await resolveModel(requestedModel)")
    w("  const send = await iii.trigger({")
    w("    function_id: 'harness::send',")
    w("    payload: {")
    w("      message: task,")
    w("      model,")
    w("      session: { title: `%s: ${task.slice(0, 50)}` }," % ns)
    w("      options: {")
    w("        system_prompt: SYSTEM_PROMPT,")
    if allow:
        w("        functions: { allow: %s }," % json.dumps(allow))
    if opts.output == "json":
        w("        output: { type: 'json', schema: OUTPUT_SCHEMA },")
    w("        max_turns: 30,")
    w("      },")
    w("    },")
    w("  })")
    w("  console.error(`[%s] session ${send.session_id} started with ${model}`)" % ns)
    w("  return new Promise((resolve, reject) => {")
    w("    const timer = setTimeout(() => {")
    w("      waiters.delete(send.session_id)")
    w("      iii.trigger({ function_id: 'harness::stop', payload: { session_id: send.session_id } }).catch(() => {})")
    w("      reject(new Error(`timed out after ${TIMEOUT_MS}ms`))")
    w("    }, TIMEOUT_MS)")
    w("    waiters.set(send.session_id, { resolve, reject, timer })")
    w("  })")
    w("}")
    w("")
    w("async function main() {")
    w("  const args = process.argv.slice(2)")
    w("  if (args[0] === '--serve') {")
    if opts.trigger == "http":
        w("    await bindHttpRoute()")
    if opts.trigger == "cron":
        w("    console.error('[%s] serving on cron %s; call %s::run to run now')" % (ns, opts.cron, ns))
    else:
        w("    console.error('[%s] serving %s::run')" % (ns, ns))
    w("    return")
    w("  }")
    w("  const task = args.join(' ').trim()")
    w("  if (!task) {")
    w("    console.error('usage: node agent.js \"task\" | node agent.js --serve')")
    w("    process.exit(1)")
    w("  }")
    w("  try {")
    w("    const result = await runTurn(task)")
    w("    console.log(typeof result === 'string' ? result : JSON.stringify(result, null, 2))")
    w("    process.exit(0)")
    w("  } catch (err) {")
    w("    console.error(`[%s] failed: ${err.message}`)" % ns)
    w("    process.exit(1)")
    w("  }")
    w("}")
    w("")
    w("main()")
    w("")
    return "\n".join(lines)


def render_package(opts):
    return json.dumps(
        {
            "name": opts.name.replace("_", "-") + "-agent",
            "version": "1.0.0",
            "private": True,
            "type": "module",
            "main": "agent.js",
            "scripts": {"start": "node agent.js --serve", "run": "node agent.js"},
            "dependencies": {"iii-sdk": "^0.21.6"},
            "engines": {"node": ">=20"},
        },
        indent=2,
    ) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", required=True,
                    help="Agent namespace: lowercase identifier, becomes <name>::run on the bus")
    ap.add_argument("--prompt", required=True,
                    help="System prompt describing the agent's job")
    ap.add_argument("--trigger", choices=["function", "cron", "http"], default="function",
                    help="How runs start: callable function only (default), cron schedule, or HTTP route")
    ap.add_argument("--cron", default="0 0 9 * * *",
                    help="6-field cron expression (sec min hour day month weekday), used with --trigger cron")
    ap.add_argument("--allow", action="append", default=[],
                    help="Function id the agent may call, e.g. web::fetch; repeatable. Omit for a pure chat loop.")
    ap.add_argument("--output", choices=["text", "json"], default="text",
                    help="Turn output contract; json adds a schema stub to edit")
    ap.add_argument("--dir", required=True, help="Output directory (created if missing)")
    opts = ap.parse_args(argv)

    if not VALID_NAME.match(opts.name):
        return fail("--name must match ^[a-z][a-z0-9_]*$, got %r" % opts.name)
    for fn in opts.allow:
        if not VALID_FUNCTION.match(fn):
            return fail("--allow %r is not a function id like web::fetch or shell::*" % fn)
    if opts.trigger == "cron" and len(opts.cron.split()) != CRON_FIELDS:
        return fail("--cron must have %d fields (sec min hour day month weekday), got %r"
                    % (CRON_FIELDS, opts.cron))

    os.makedirs(opts.dir, exist_ok=True)
    agent_path = os.path.join(opts.dir, "agent.js")
    package_path = os.path.join(opts.dir, "package.json")
    for path in (agent_path, package_path):
        if os.path.exists(path):
            return fail("%s already exists; refusing to overwrite" % path)

    with open(agent_path, "w") as f:
        f.write(render_agent(opts))
    with open(package_path, "w") as f:
        f.write(render_package(opts))

    print(agent_path)
    print(package_path)
    print("next: npm install, then node agent.js \"a task\" (engine + harness worker must be running)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
