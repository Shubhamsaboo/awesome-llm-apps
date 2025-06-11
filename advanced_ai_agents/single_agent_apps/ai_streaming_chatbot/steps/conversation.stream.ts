import { StreamConfig } from 'motia'
import { z } from 'zod'

export const conversationSchema = z.object({
  message: z.string(),
  from: z.enum(['user', 'assistant']),
  status: z.enum(['created', 'streaming', 'completed']),
  timestamp: z.string(),
})

export const config: StreamConfig = {
  name: 'conversation',
  schema: conversationSchema,
  baseConfig: { storageType: 'default' },
}
