import { ApiRouteConfig, Handlers } from 'motia'
import { z } from 'zod'

const inputSchema = z.object({
  message: z.string().min(1, 'Message is required'),
  conversationId: z.string().optional(),
})

export const config: ApiRouteConfig = {
  type: 'api',
  name: 'ChatApi',
  description: 'Send a message to the AI chatbot',
  path: '/chat',
  method: 'POST',
  emits: ['chat-message'],
  bodySchema: inputSchema,
  responseSchema: {
    200: z.object({
      conversationId: z.string(),
      message: z.string(),
      status: z.enum(['created', 'streaming', 'completed']).optional(),
    })
  },
  flows: ['chat'],
}

export const handler: Handlers['ChatApi'] = async (req, { logger, emit, streams }) => {
  const conversationId = req.body.conversationId || crypto.randomUUID()
  const userMessageId = crypto.randomUUID()
  const assistantMessageId = crypto.randomUUID()

  logger.info('New chat message received', { 
    conversationId,
    message: req.body.message 
  })

  await streams.conversation.set(conversationId, userMessageId, {
    message: req.body.message,
    from: 'user',
    status: 'completed',
    timestamp: new Date().toISOString(),
  })

  await streams.conversation.set(conversationId, assistantMessageId, {
    message: '',
    from: 'assistant',
    status: 'created',
    timestamp: new Date().toISOString(),
  })

  await emit({
    topic: 'chat-message',
    data: {
      message: req.body.message,
      conversationId,
      assistantMessageId,
    },
  })

  const maxWaitTime = 3000 // 3 seconds
  const startTime = Date.now()
  let aiResponse = null

  // Initial delay to allow AI to start processing
  await new Promise(resolve => setTimeout(resolve, 100))

  while (Date.now() - startTime < maxWaitTime) {
    const response = await streams.conversation.get(conversationId, assistantMessageId)
    if (response) {
      aiResponse = response
      // Break only if we have a completed status
      if (response.status === 'completed') {
        break
      }
    }
    await new Promise(resolve => setTimeout(resolve, 100))
  }

  // Get final response state
  if (!aiResponse?.status || aiResponse.status !== 'completed') {
    const finalResponse = await streams.conversation.get(conversationId, assistantMessageId)
    if (finalResponse?.status === 'completed') {
      aiResponse = finalResponse
    }
  }

  logger.info('Returning chat response', { 
    conversationId,
    messageId: assistantMessageId,
    status: aiResponse?.status,
    hasMessage: !!aiResponse?.message
  })

  return {
    status: 200,
    body: {
      conversationId,
      message: aiResponse?.status === 'completed' ? aiResponse.message : 'Message received, AI is responding...',
      status: aiResponse?.status || 'streaming',
    },
  }
}
