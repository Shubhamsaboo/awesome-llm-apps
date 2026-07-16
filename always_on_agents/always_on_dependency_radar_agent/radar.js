import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { registerWorker } from 'iii-sdk'

const ENGINE_URL = process.env.III_URL || 'ws://localhost:49134'
const CRON_EXPRESSION = process.env.RADAR_CRON || '0 0 9 * * *'
const TIMEOUT_MS = Number(process.env.RADAR_TIMEOUT_MS || 5 * 60 * 1000)
const MAX_RESEARCH = Number(process.env.RADAR_MAX_RESEARCH || 6)
const TARGET = resolve(process.env.RADAR_PACKAGE_JSON || './package.json')
const WEBHOOK_URL = process.env.RADAR_WEBHOOK_URL || ''
const DIGESTS_SCOPE = 'radar::digests'

const DIGEST_SCHEMA = {
  type: 'object',
  required: ['summary', 'packages'],
  properties: {
    summary: {
      type: 'string',
      description: 'Two or three sentences: how urgent is this upgrade batch overall.',
    },
    packages: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'current', 'latest', 'risk', 'notes'],
        properties: {
          name: { type: 'string' },
          current: { type: 'string' },
          latest: { type: 'string' },
          risk: { type: 'string', enum: ['safe', 'review', 'breaking'] },
          notes: {
            type: 'string',
            description: 'What changed and what the upgrade requires, grounded in the changelog.',
          },
          changelog_url: { type: 'string' },
        },
      },
    },
  },
}

const ANALYST_PROMPT = `You are a dependency upgrade analyst. You receive a list
of outdated npm packages with their current and latest versions. For each one:
1. Find its repository URL with web::fetch on
   https://registry.npmjs.org/<name>/latest (pass response_format: "json").
   Never fetch https://registry.npmjs.org/<name> without the /latest suffix:
   the full package document is megabytes.
2. Read the release notes or changelog for the versions between current and
   latest with web::fetch using format: "markdown". GitHub releases live at
   https://github.com/<owner>/<repo>/releases.
3. Classify the upgrade: "safe" (patches, fixes only), "review" (new features
   or deprecations worth reading), or "breaking" (major bump or documented
   breaking changes).
4. Write notes a maintainer can act on: name the specific breaking changes and
   migration steps, not generic advice.
Pass max_bytes: 30000 on every web::fetch call so oversized pages come back
truncated instead of flooding the session.
Only report what the changelogs actually say. If you cannot find release notes
for a package, say so in its notes and classify it "review".`

const iii = registerWorker(ENGINE_URL)
const waiters = new Map()

iii.registerFunction(
  'radar::scan',
  async () => runScan(),
  {
    description:
      'Scan the configured package.json against the npm registry, have a harness agent read the changelogs of every outdated dependency, and store an upgrade-risk digest in state.',
    response_format: {
      type: 'object',
      body: {
        outdated: { type: 'integer' },
        digest_key: { type: 'string', description: 'state key of the stored digest' },
      },
    },
  },
)

iii.registerFunction(
  'radar::digest',
  async (input) => {
    const key = (typeof input === 'string' ? input : input?.key) || 'latest'
    return iii.trigger({
      function_id: 'state::get',
      payload: { scope: DIGESTS_SCOPE, key },
    })
  },
  {
    description: 'Fetch a stored dependency digest by date key (defaults to "latest").',
    request_format: {
      type: 'object',
      body: { key: { type: 'string', description: 'YYYY-MM-DD or "latest"' } },
    },
  },
)

iii.registerFunction('radar::on-turn-completed', async (event) => {
  const waiter = waiters.get(event?.session_id)
  if (!waiter) return {}
  waiters.delete(event.session_id)
  clearTimeout(waiter.timer)
  if (event.status === 'completed' && event.result !== undefined) {
    waiter.resolve(event.result)
  } else {
    waiter.reject(
      new Error(`radar turn ${event.status}: ${event.result_error || event.reason || 'no result'}`),
    )
  }
  return {}
})

iii.registerFunction('radar::api::digest', async (req) => {
  const digest = await iii.trigger({
    function_id: 'state::get',
    payload: { scope: DIGESTS_SCOPE, key: req?.path_params?.key || 'latest' },
  })
  if (!digest) return { status_code: 404, body: { error: 'no digest stored yet' } }
  return { status_code: 200, body: digest }
})

iii.registerFunction('radar::api::scan', async () => {
  const result = await runScan()
  return { status_code: 200, body: result }
})

iii.registerTrigger({
  type: 'harness::turn-completed',
  function_id: 'radar::on-turn-completed',
  config: {},
})

iii.registerTrigger({
  type: 'cron',
  function_id: 'radar::scan',
  config: { expression: CRON_EXPRESSION },
})

async function bindHttpRoutes() {
  try {
    await iii.trigger({
      function_id: 'engine::register_trigger',
      payload: {
        trigger_type: 'http',
        function_id: 'radar::api::digest',
        config: { api_path: '/radar/digest', http_method: 'GET' },
      },
    })
    await iii.trigger({
      function_id: 'engine::register_trigger',
      payload: {
        trigger_type: 'http',
        function_id: 'radar::api::scan',
        config: { api_path: '/radar/scan', http_method: 'POST' },
      },
    })
    console.error('[radar] REST routes live: GET /radar/digest, POST /radar/scan')
  } catch {
    console.error('[radar] http worker not installed, REST routes skipped (iii worker add http)')
  }
}

async function resolveModel() {
  if (process.env.RADAR_MODEL) return process.env.RADAR_MODEL
  const { models = [] } = await iii.trigger({ function_id: 'router::models::list', payload: {} })
  const usable = models.filter((m) => m.supports_tools).map((m) => m.id)
  if (usable.length === 1) return usable[0]
  if (usable.length === 0) {
    throw new Error(
      'no models available: configure a provider in llm-router (console model picker, or iii worker add provider-anthropic / provider-openai / provider-xai / ...)',
    )
  }
  throw new Error(
    `several models are available; set RADAR_MODEL to one of:\n  ${usable.join('\n  ')}`,
  )
}

function readManifest() {
  const manifest = JSON.parse(readFileSync(TARGET, 'utf8'))
  return {
    name: manifest.name || TARGET,
    deps: { ...manifest.dependencies, ...manifest.devDependencies },
  }
}

async function collectOutdated() {
  const { name, deps } = readManifest()
  const outdated = []
  for (const [pkg, declared] of Object.entries(deps)) {
    const current = String(declared).replace(/^[\^~>=<\s]+/, '')
    if (!/^\d/.test(current)) continue
    const res = await iii.trigger({
      function_id: 'web::fetch',
      payload: {
        url: `https://registry.npmjs.org/${encodeURIComponent(pkg)}/latest`,
        response_format: 'json',
      },
    })
    if (!res?.ok || !res?.json?.version) {
      console.error(`[radar] could not resolve latest version of ${pkg}, skipping`)
      continue
    }
    if (isBehind(current, res.json.version)) {
      outdated.push({ name: pkg, current, latest: res.json.version })
    }
  }
  outdated.sort((a, b) => versionGap(b) - versionGap(a))
  return { name, total: Object.keys(deps).length, outdated }
}

function parseVersion(v) {
  const m = String(v).match(/^(\d+)\.(\d+)\.(\d+)/)
  return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null
}

function isBehind(current, latest) {
  const c = parseVersion(current)
  const l = parseVersion(latest)
  if (!c || !l) return false
  for (let i = 0; i < 3; i++) {
    if (l[i] > c[i]) return true
    if (l[i] < c[i]) return false
  }
  return false
}

function versionGap(pkg) {
  const c = parseVersion(pkg.current)
  const l = parseVersion(pkg.latest)
  if (!c || !l) return 0
  return (l[0] - c[0]) * 10000 + (l[1] - c[1]) * 100 + (l[2] - c[2])
}

async function analyzeWithAgent(scan) {
  const model = await resolveModel()
  const toResearch = scan.outdated.slice(0, MAX_RESEARCH)
  const skipped = scan.outdated.slice(MAX_RESEARCH)
  if (skipped.length > 0) {
    console.error(
      `[radar] researching the ${toResearch.length} most-behind packages; ${skipped.length} more listed without changelog research (RADAR_MAX_RESEARCH=${MAX_RESEARCH})`,
    )
  }
  const send = await iii.trigger({
    function_id: 'harness::send',
    payload: {
      message: `Outdated dependencies of ${scan.name}:\n${JSON.stringify(toResearch, null, 2)}`,
      model,
      session: { title: `dependency radar: ${scan.name}` },
      options: {
        system_prompt: ANALYST_PROMPT,
        functions: { allow: ['web::fetch'] },
        output: { type: 'json', schema: DIGEST_SCHEMA },
        max_turns: 30,
      },
    },
  })
  console.error(
    `[radar] session ${send.session_id} analyzing ${toResearch.length} packages with ${model}`,
  )
  const digest = await new Promise((resolvePromise, reject) => {
    const timer = setTimeout(() => {
      waiters.delete(send.session_id)
      iii
        .trigger({ function_id: 'harness::stop', payload: { session_id: send.session_id } })
        .catch(() => {})
      reject(new Error(`radar analysis timed out after ${TIMEOUT_MS}ms`))
    }, TIMEOUT_MS)
    waiters.set(send.session_id, { resolve: resolvePromise, reject, timer })
  })
  digest.skipped = skipped
  return digest
}

async function runScan() {
  const scan = await collectOutdated()
  if (scan.outdated.length === 0) {
    console.error(`[radar] ${scan.name}: all ${scan.total} dependencies up to date`)
    return { outdated: 0, digest_key: null }
  }
  const digest = await analyzeWithAgent(scan)
  const key = new Date().toISOString().slice(0, 10)
  const record = { date: key, project: scan.name, ...digest }
  for (const k of [key, 'latest']) {
    await iii.trigger({
      function_id: 'state::set',
      payload: { scope: DIGESTS_SCOPE, key: k, value: record },
    })
  }
  await deliverWebhook(record)
  console.error(`[radar] digest stored: state::get { scope: "${DIGESTS_SCOPE}", key: "${key}" }`)
  return { outdated: scan.outdated.length, digest_key: key }
}

async function deliverWebhook(digest) {
  if (!WEBHOOK_URL) return
  const breaking = digest.packages.filter((p) => p.risk === 'breaking').length
  await iii.trigger({
    function_id: 'web::fetch',
    payload: {
      url: WEBHOOK_URL,
      method: 'POST',
      json: {
        text: `Dependency radar for ${digest.project}: ${digest.packages.length} outdated, ${breaking} breaking. ${digest.summary}`,
      },
    },
  })
  console.error('[radar] webhook delivered')
}

async function main() {
  const args = process.argv.slice(2)
  if (args[0] === '--serve') {
    await bindHttpRoutes()
    console.error(`[radar] watching ${TARGET} on cron "${CRON_EXPRESSION}"`)
    return
  }
  try {
    const result = await runScan()
    if (result.outdated > 0) {
      const digest = await iii.trigger({
        function_id: 'state::get',
        payload: { scope: DIGESTS_SCOPE, key: 'latest' },
      })
      console.log(JSON.stringify(digest, null, 2))
    }
    process.exit(0)
  } catch (err) {
    console.error(`[radar] failed: ${err.message}`)
    process.exit(1)
  }
}

main()
