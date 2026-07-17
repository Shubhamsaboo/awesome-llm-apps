import readline from 'node:readline/promises'
import { registerWorker } from 'iii-sdk'

const ENGINE_URL = process.env.III_URL || 'ws://localhost:49134'
const SYSTEM_PROMPT =
  process.env.CHAT_SYSTEM_PROMPT ||
  'You are a helpful AI assistant. Keep responses concise and friendly.'
const ALLOWED_FUNCTIONS = (process.env.CHAT_FUNCTIONS || '')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean)

const iii = registerWorker(ENGINE_URL)

iii.registerFunction(
  'chat::send',
  async (input) => {
    const message = typeof input === 'string' ? input : input?.message
    if (!message) throw new Error('chat::send requires { message: string }')
    return sendMessage(message, input?.conversation_id, input?.model)
  },
  {
    description:
      'Send a chat message. Omit conversation_id to start a new conversation; pass it back to continue one. The reply streams into the session transcript.',
    request_format: {
      type: 'object',
      body: {
        message: { type: 'string' },
        conversation_id: { type: 'string', description: 'Continue an existing conversation' },
        model: { type: 'string', description: 'Model id from router::models::list' },
      },
    },
    response_format: {
      type: 'object',
      body: {
        conversation_id: { type: 'string' },
        turn_id: { type: 'string' },
      },
    },
  },
)

iii.registerFunction(
  'chat::history',
  async (input) => {
    const conversationId = typeof input === 'string' ? input : input?.conversation_id
    if (!conversationId) throw new Error('chat::history requires { conversation_id: string }')
    const transcript = await iii.trigger({
      function_id: 'session::messages',
      payload: { session_id: conversationId },
    })
    const messages = (transcript?.messages || [])
      .map((entry) => entry.message || entry)
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .map((m) => ({ role: m.role, text: blocksText(m.content) }))
      .filter((m) => m.text)
    return { conversation_id: conversationId, messages }
  },
  {
    description:
      'Fetch a conversation transcript as [{role, text}]. While a reply is streaming, the partial assistant text is already in it.',
    request_format: {
      type: 'object',
      body: { conversation_id: { type: 'string' } },
    },
  },
)

iii.registerFunction('chat::api::send', async (req) => {
  const message = req?.body?.message
  if (!message) {
    return { status_code: 400, body: { error: 'POST a JSON body: { "message": "..." }' } }
  }
  const sent = await sendMessage(message, req?.body?.conversation_id, req?.body?.model)
  return { status_code: 202, body: { ...sent, history: `GET /chat/${sent.conversation_id}` } }
})

iii.registerFunction('chat::api::history', async (req) => {
  const conversationId = req?.path_params?.conversation_id
  try {
    const history = await iii.trigger({
      function_id: 'chat::history',
      payload: { conversation_id: conversationId },
    })
    return { status_code: 200, body: history }
  } catch {
    return { status_code: 404, body: { error: 'unknown conversation_id' } }
  }
})

function blocksText(content) {
  return (Array.isArray(content) ? content : [])
    .filter((b) => b.type === 'text')
    .map((b) => b.text)
    .join('')
}

async function resolveModel(requested) {
  if (requested) return requested
  if (process.env.CHAT_MODEL) return process.env.CHAT_MODEL
  const { models = [] } = await iii.trigger({ function_id: 'router::models::list', payload: {} })
  const usable = models.filter((m) => m.supports_tools).map((m) => m.id)
  if (usable.length === 1) return usable[0]
  if (usable.length === 0) {
    throw new Error(
      'no models available: configure a provider in llm-router (console model picker, or iii worker add provider-anthropic / provider-openai / provider-xai / ...)',
    )
  }
  throw new Error(
    `several models are available; set CHAT_MODEL to one of:\n  ${usable.join('\n  ')}`,
  )
}

async function sendMessage(message, conversationId, requestedModel) {
  const model = await resolveModel(requestedModel)
  const send = await iii.trigger({
    function_id: 'harness::send',
    payload: {
      message,
      model,
      session_id: conversationId,
      session: { title: `chat: ${message.slice(0, 50)}` },
      options: {
        system_prompt: SYSTEM_PROMPT,
        system_prompt_strategy: ALLOWED_FUNCTIONS.length ? 'enrich' : 'override',
        ...(ALLOWED_FUNCTIONS.length
          ? { mode: 'agent', functions: { allow: ALLOWED_FUNCTIONS } }
          : { mode: 'ask' }),
      },
    },
  })
  return { conversation_id: send.session_id, turn_id: send.turn_id }
}

async function bindHttpRoutes() {
  try {
    await iii.trigger({
      function_id: 'engine::register_trigger',
      payload: {
        trigger_type: 'http',
        function_id: 'chat::api::send',
        config: { api_path: '/chat', http_method: 'POST' },
      },
    })
    await iii.trigger({
      function_id: 'engine::register_trigger',
      payload: {
        trigger_type: 'http',
        function_id: 'chat::api::history',
        config: { api_path: '/chat/:conversation_id', http_method: 'GET' },
      },
    })
    console.error('[chat] REST routes live: POST /chat, GET /chat/:conversation_id')
  } catch {
    console.error('[chat] http worker not installed, REST routes skipped (iii worker add http)')
  }
}

async function repl() {
  let conversationId = null
  let currentTurnId = null
  let printed = 0
  let turnDone = null

  iii.registerFunction('chat::cli::on-update', async (event) => {
    if (!currentTurnId || event?.origin?.turn_id !== currentTurnId) return {}
    const text = blocksText(event.message?.content)
    if (text.length > printed) {
      process.stdout.write(text.slice(printed))
      printed = text.length
    }
    return {}
  })

  iii.registerFunction('chat::cli::on-completed', async (event) => {
    if (event?.turn_id === currentTurnId && turnDone) turnDone(event)
    return {}
  })

  for (const triggerType of ['session::message-added', 'session::message-updated']) {
    await iii.trigger({
      function_id: 'engine::register_trigger',
      payload: {
        trigger_type: triggerType,
        function_id: 'chat::cli::on-update',
        config: { roles: ['assistant'] },
      },
    })
  }
  await iii.trigger({
    function_id: 'engine::register_trigger',
    payload: {
      trigger_type: 'harness::turn-completed',
      function_id: 'chat::cli::on-completed',
      config: {},
    },
  })

  console.error('[chat] streaming chatbot ready, empty line exits')
  if (ALLOWED_FUNCTIONS.length) console.error(`[chat] agent functions: ${ALLOWED_FUNCTIONS.join(', ')}`)
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout })
  process.stdout.write('\nyou > ')
  for await (const raw of rl) {
    const line = raw.trim()
    if (!line) break
    printed = 0
    const done = new Promise((resolve) => {
      turnDone = resolve
    })
    process.stdout.write('ai  > ')
    const sent = await sendMessage(line, conversationId)
    conversationId = sent.conversation_id
    currentTurnId = sent.turn_id
    const event = await done
    turnDone = null
    currentTurnId = null
    if (event.status !== 'completed') {
      console.error(`\n[chat] turn ${event.status}: ${event.result_error || event.reason || ''}`)
    } else {
      const finalText = typeof event.result === 'string' ? event.result : ''
      if (finalText.length > printed) process.stdout.write(finalText.slice(printed))
      process.stdout.write('\n')
    }
    process.stdout.write('\nyou > ')
  }
  rl.close()
  process.exit(0)
}

async function main() {
  const args = process.argv.slice(2)
  if (args[0] === '--serve') {
    await bindHttpRoutes()
    console.error('[chat] serving chat::send / chat::history')
    return
  }
  await repl()
}

main()
