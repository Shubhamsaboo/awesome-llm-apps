import { registerWorker } from 'iii-sdk'

const ENGINE_URL = process.env.III_URL || 'ws://localhost:49134'
const TIMEOUT_MS = Number(process.env.RESEARCH_TIMEOUT_MS || 10 * 60 * 1000)
const REPORTS_SCOPE = 'research::reports'

const REPORT_SCHEMA = {
  type: 'object',
  required: ['answer', 'key_findings', 'sources'],
  properties: {
    answer: {
      type: 'string',
      description: 'The synthesized answer to the research question, 3-6 paragraphs.',
    },
    key_findings: {
      type: 'array',
      items: { type: 'string' },
      description: 'The most important discrete facts uncovered, one sentence each.',
    },
    sources: {
      type: 'array',
      items: {
        type: 'object',
        required: ['url', 'title'],
        properties: {
          url: { type: 'string' },
          title: { type: 'string' },
          used_for: { type: 'string' },
        },
      },
    },
  },
}

const ORCHESTRATOR_PROMPT = `You are the lead researcher of a research team.
You delegate all reading: you MUST NOT call web::fetch yourself, ever. It is
in your allow-list only so you can grant it to the researchers you spawn (a
sub-agent can never hold a function its parent does not hold). Your own calls
are harness::spawn and nothing else.

Process for every research question:
1. Break the question into distinct research angles. You decide how many
   researchers the question needs based on its breadth: a narrow factual
   question may need one, a broad comparative question may need four or five.
2. Spawn one sub-agent per angle with harness::spawn. Each spawn payload must
   contain a "task" string that fully describes that researcher's assignment,
   the specific claims to verify, and an instruction to cite the URL of every
   page it relies on. Pass options.functions.allow = ["web::fetch"] on every
   spawn so researchers can read the web but cannot spawn further agents.
3. Researchers read pages with web::fetch using format: "markdown" and
   max_bytes: 40000 on every call, so oversized pages come back truncated
   instead of flooding their session. Include both instructions in every task
   string.
4. When all researchers return, cross-check their findings against each other.
   If two researchers disagree on a fact, spawn one more researcher to settle
   the disagreement with primary sources before you write the report.
5. Produce the final report in the required JSON shape. Every entry in
   key_findings must be traceable to at least one entry in sources.

Never answer from your own knowledge alone: every key finding must come from
a page a researcher actually fetched.`

const iii = registerWorker(ENGINE_URL)
const waiters = new Map()

iii.registerFunction(
  'research::start',
  async (input) => {
    const question = typeof input === 'string' ? input : input?.question
    if (!question) throw new Error('research::start requires { question: string }')
    return startResearch(question, input?.model)
  },
  {
    description:
      'Start a multi-agent deep research run: an orchestrator turn spawns researcher sub-agents, cross-checks their findings, and stores a cited JSON report in state. Returns immediately; read the report with research::report.',
    request_format: {
      type: 'object',
      body: {
        question: { type: 'string', description: 'The research question' },
        model: { type: 'string', description: 'Model id from router::models::list; optional when only one is available' },
      },
    },
    response_format: {
      type: 'object',
      body: {
        session_id: { type: 'string' },
        turn_id: { type: 'string' },
      },
    },
  },
)

iii.registerFunction(
  'research::report',
  async (input) => {
    const sessionId = typeof input === 'string' ? input : input?.session_id
    if (!sessionId) throw new Error('research::report requires { session_id: string }')
    return iii.trigger({
      function_id: 'state::get',
      payload: { scope: REPORTS_SCOPE, key: sessionId },
    })
  },
  {
    description: 'Fetch a stored research report by session_id (null until the run completes).',
    request_format: {
      type: 'object',
      body: { session_id: { type: 'string' } },
    },
  },
)

iii.registerFunction('research::on-turn-completed', async (event) => {
  const sessionId = event?.session_id
  if (!sessionId) return {}
  const running = await iii.trigger({
    function_id: 'state::get',
    payload: { scope: REPORTS_SCOPE, key: sessionId },
  })
  if (!running || running.status !== 'running') return {}
  const record =
    event.status === 'completed' && event.result !== undefined
      ? { status: 'completed', question: running.question, report: event.result }
      : {
          status: 'failed',
          question: running.question,
          error: event.result_error || event.reason || event.status,
        }
  await iii.trigger({
    function_id: 'state::set',
    payload: { scope: REPORTS_SCOPE, key: sessionId, value: record },
  })
  const waiter = waiters.get(sessionId)
  if (waiter) {
    waiters.delete(sessionId)
    clearTimeout(waiter.timer)
    if (record.status === 'completed') waiter.resolve(record.report)
    else waiter.reject(new Error(`research ${record.status}: ${record.error}`))
  }
  return {}
})

iii.registerFunction('research::api::start', async (req) => {
  const question = req?.body?.question
  if (!question) {
    return { status_code: 400, body: { error: 'POST a JSON body: { "question": "..." }' } }
  }
  const started = await startResearch(question, req?.body?.model)
  return {
    status_code: 202,
    body: { ...started, report: `GET /research/${started.session_id}` },
  }
})

iii.registerFunction('research::api::report', async (req) => {
  const record = await iii.trigger({
    function_id: 'state::get',
    payload: { scope: REPORTS_SCOPE, key: req?.path_params?.session_id },
  })
  if (!record) return { status_code: 404, body: { error: 'unknown session_id' } }
  return { status_code: record.status === 'running' ? 202 : 200, body: record }
})

iii.registerTrigger({
  type: 'harness::turn-completed',
  function_id: 'research::on-turn-completed',
  config: {},
})

async function bindHttpRoutes() {
  try {
    await iii.trigger({
      function_id: 'engine::register_trigger',
      payload: {
        trigger_type: 'http',
        function_id: 'research::api::start',
        config: { api_path: '/research', http_method: 'POST' },
      },
    })
    await iii.trigger({
      function_id: 'engine::register_trigger',
      payload: {
        trigger_type: 'http',
        function_id: 'research::api::report',
        config: { api_path: '/research/:session_id', http_method: 'GET' },
      },
    })
    console.error('[research] REST routes live: POST /research, GET /research/:session_id')
  } catch {
    console.error('[research] http worker not installed, REST routes skipped (iii worker add http)')
  }
}

async function resolveModel(requested) {
  if (requested) return requested
  if (process.env.RESEARCH_MODEL) return process.env.RESEARCH_MODEL
  const { models = [] } = await iii.trigger({ function_id: 'router::models::list', payload: {} })
  const usable = models.filter((m) => m.supports_tools).map((m) => m.id)
  if (usable.length === 1) return usable[0]
  if (usable.length === 0) {
    throw new Error(
      'no models available: configure a provider in llm-router (console model picker, or iii worker add provider-anthropic / provider-openai / provider-xai / ...)',
    )
  }
  throw new Error(
    `several models are available; pass a model or set RESEARCH_MODEL to one of:\n  ${usable.join('\n  ')}`,
  )
}

async function startResearch(question, requestedModel) {
  const model = await resolveModel(requestedModel)
  const send = await iii.trigger({
    function_id: 'harness::send',
    payload: {
      message: `Research question: ${question}`,
      model,
      session: { title: `research: ${question.slice(0, 60)}` },
      options: {
        system_prompt: ORCHESTRATOR_PROMPT,
        functions: { allow: ['harness::spawn', 'web::fetch'] },
        output: { type: 'json', schema: REPORT_SCHEMA },
        max_turns: 40,
      },
    },
  })
  await iii.trigger({
    function_id: 'state::set',
    payload: {
      scope: REPORTS_SCOPE,
      key: send.session_id,
      value: { status: 'running', question },
    },
  })
  console.error(`[research] session ${send.session_id} started with ${model}`)
  return { session_id: send.session_id, turn_id: send.turn_id }
}

function waitForReport(sessionId) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      waiters.delete(sessionId)
      iii
        .trigger({ function_id: 'harness::stop', payload: { session_id: sessionId } })
        .catch(() => {})
      reject(new Error(`research timed out after ${TIMEOUT_MS}ms`))
    }, TIMEOUT_MS)
    waiters.set(sessionId, { resolve, reject, timer })
  })
}

async function main() {
  const args = process.argv.slice(2)
  if (args[0] === '--serve') {
    await bindHttpRoutes()
    console.error('[research] serving research::start / research::report')
    return
  }
  const modelFlag = args.indexOf('--model')
  let model
  if (modelFlag !== -1) {
    model = args[modelFlag + 1]
    args.splice(modelFlag, 2)
  }
  const question = args.join(' ').trim()
  if (!question) {
    console.error('usage: node agent_team.js "your research question" [--model <id>]')
    console.error('       node agent_team.js --serve')
    process.exit(1)
  }
  try {
    const { session_id } = await startResearch(question, model)
    const report = await waitForReport(session_id)
    console.log(JSON.stringify(report, null, 2))
    process.exit(0)
  } catch (err) {
    console.error(`[research] failed: ${err.message}`)
    process.exit(1)
  }
}

main()
