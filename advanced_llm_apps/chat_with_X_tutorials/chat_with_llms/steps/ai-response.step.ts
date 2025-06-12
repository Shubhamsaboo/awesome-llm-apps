import { EventConfig, Handlers } from 'motia'
import { OpenAI } from 'openai'
import { z } from 'zod'
// import { AzureOpenAI } from 'openai'

export const config: EventConfig = {
  type: 'event',
  name: 'AiResponse',
  description: 'Generate streaming AI response',
  subscribes: ['chat-message'],
  emits: [],
  input: z.object({
    message: z.string(),
    conversationId: z.string(),
    assistantMessageId: z.string(),
  }),
  flows: ['chat'],
}

export const handler: Handlers['AiResponse'] = async (input, context) => {
  const { logger, streams } = context
  const { message, conversationId, assistantMessageId } = input

  logger.info('Generating AI response', { conversationId })

  // For Azure OpenAI
  // const openai = new AzureOpenAI({
  //   endpoint: process.env.AZURE_OPENAI_ENDPOINT || 'demo-key',
  //   apiKey: process.env.AZURE_OPENAI_API_KEY || 'demo-key',
  //   deployment: 'gpt-4o-mini',
  //   apiVersion: '2024-12-01-preview'
  // })

  const openai = new OpenAI({ 
    apiKey: process.env.OPENAI_API_KEY,
    baseURL: process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1'
  })

  try {
    await streams.conversation.set(conversationId, assistantMessageId, {
      message: '',
      from: 'assistant',
      status: 'streaming',
      timestamp: new Date().toISOString(),
    })

    const stream = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: 'You are a helpful AI assistant. Keep responses concise and friendly.'
        },
        {
          role: 'user',
          content: message
        }
      ],
      stream: true,
    })

    let fullResponse = ''

    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content || ''
      if (content) {
        fullResponse += content
        
        await streams.conversation.set(conversationId, assistantMessageId, {
          message: fullResponse,
          from: 'assistant',
          status: 'streaming',
          timestamp: new Date().toISOString(),
        })
      }
    }

    await streams.conversation.set(conversationId, assistantMessageId, {
      message: fullResponse,
      from: 'assistant',
      status: 'completed',
      timestamp: new Date().toISOString(),
    })

    logger.info('AI response completed', { 
      conversationId,
      responseLength: fullResponse.length 
    })

  } catch (error) {
    logger.error('Error generating AI response', { error, conversationId })
    
    await streams.conversation.set(conversationId, assistantMessageId, {
      message: 'Sorry, I encountered an error. Please try again.',
      from: 'assistant',
      status: 'completed',
      timestamp: new Date().toISOString(),
    })
  }
}
