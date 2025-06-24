# Streaming AI Chatbot

A minimal example demonstrating **real-time AI streaming** and **conversation state management** using the Motia framework.
![streaming-ai-chatbot](docs/images/streaming-ai-chatbot.gif)

## 🚀 Features

- **Real-time AI Streaming**: Token-by-token response generation using OpenAI's streaming API
- **Live State Management**: Conversation state updates in real-time with message history
- **Event-driven Architecture**: Clean API → Event → Streaming Response flow
- **Minimal Complexity**: Maximum impact with just 3 core files

## 📁 Architecture

```
streaming-ai-chatbot/
├── steps/
│   ├── conversation.stream.ts    # Real-time conversation state
│   ├── chat-api.step.ts         # Simple chat API endpoint  
│   └── ai-response.step.ts      # Streaming AI response handler
├── package.json                 # Dependencies
├── .env.example                 # Configuration template
└── README.md                    # This file
```

## 🛠️ Setup

### Installation & Setup

```bash
# Clone the repository
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_llm_apps/chat_with_X_tutorials/chat_with_llms

# Install dependencies
npm install

# Start the development server
npm run dev
```

### Configure OpenAI API
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

**Open Motia Workbench**:
   Navigate to `http://localhost:3000` to interact with the chatbot

## 🔧 Usage

### Send a Chat Message

**POST** `/chat`

```json
{
  "message": "Hello, how are you?",
  "conversationId": "optional-conversation-id"  // Optional: If not provided, a new conversation will be created
}
```

**Response:**
```json
{
  "conversationId": "uuid-v4",
  "message": "Message received, AI is responding...",
  "status": "streaming"
}
```

The response will update as the AI processes the message, with possible status values:
- `created`: Initial message state
- `streaming`: AI is generating the response
- `completed`: Response is complete with full message

When completed, the response will contain the actual AI message instead of the processing message.

### Real-time State Updates

The conversation state stream provides live updates as the AI generates responses:

- **User messages**: Immediately stored with `status: 'completed'`
- **AI responses**: Start with `status: 'streaming'`, update in real-time, end with `status: 'completed'`

## 🎯 Key Concepts Demonstrated

### 1. **Streaming API Integration**
```typescript
const stream = await openai.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [...],
  stream: true, // Enable streaming
})

for await (const chunk of stream) {
  // Update state with each token
  await streams.conversation.set(conversationId, messageId, {
    message: fullResponse,
    status: 'streaming',
    // ...
  })
}
```

### 2. **Real-time State Management**
```typescript
export const config: StateStreamConfig = {
  name: 'conversation',
  schema: z.object({
    message: z.string(),
    from: z.enum(['user', 'assistant']),
    status: z.enum(['created', 'streaming', 'completed']),
    timestamp: z.string(),
  }),
  baseConfig: { storageType: 'state' },
}
```

### 3. **Event-driven Flow**
```typescript
// API emits event
await emit({
  topic: 'chat-message',
  data: { message, conversationId, assistantMessageId },
})

// Event handler subscribes and processes
export const config: EventConfig = {
  subscribes: ['chat-message'],
  // ...
}
```

## 🌟 Why This Example Matters

This example showcases Motia's power in just **3 files**:

- **Effortless streaming**: Real-time AI responses with automatic state updates
- **Type-safe events**: End-to-end type safety from API to event handlers
- **Built-in state management**: No external state libraries needed
- **Scalable architecture**: Event-driven design that grows with your needs

Perfect for demonstrating how Motia makes complex real-time applications simple and maintainable.

## 🔑 Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)