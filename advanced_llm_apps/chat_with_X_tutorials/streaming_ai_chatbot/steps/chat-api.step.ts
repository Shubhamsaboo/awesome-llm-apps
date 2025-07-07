import { ApiRouteConfig, Handlers } from 'motia'
import { z } from 'zod'
import { conversationSchema } from './conversation.stream'

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
    200: conversationSchema
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

  const aiResponse = await streams.conversation.set(conversationId, assistantMessageId, {
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

  logger.info('Returning chat response', { 
    conversationId,
    messageId: assistantMessageId,
  })

  return {
    status: 200,
    body: aiResponse,
  }
}
