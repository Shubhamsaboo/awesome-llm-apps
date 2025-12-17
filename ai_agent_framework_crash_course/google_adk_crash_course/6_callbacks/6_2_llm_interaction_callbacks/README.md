# 6.2 LLM Interaction Callbacks

This tutorial demonstrates how to use `before_model_callback` and `after_model_callback` to monitor LLM requests and responses.

## 🎯 Learning Objectives

- Understand LLM interaction callbacks
- Learn how to monitor LLM requests and responses
- Track token usage and response times
- Estimate API costs
- Monitor LLM performance metrics

## 📁 Project Structure

```
6_2_llm_interaction_callbacks/
├── agent.py          # Agent with LLM interaction callbacks
├── app.py            # Streamlit web interface
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## 🔧 Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API key:**
   ```bash
   # Create .env file
   echo "GOOGLE_API_KEY=your_api_key_here" > .env
   ```

## 🚀 Running the Demo

### Command Line Demo
```bash
python agent.py
```

### Web Interface
```bash
streamlit run app.py
```

## 🧠 Core Concept: LLM Interaction Monitoring

LLM interaction callbacks allow you to monitor the communication between your agent and the underlying language model, providing insights into requests, responses, and performance metrics.

### **LLM Interaction Flow**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  LLM Request    │───▶│  LLM Response   │
│                 │    │   Callback      │    │   Callback      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                       │
                              ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Model API      │    │  Token Usage    │
                       │  (Gemini)       │    │  & Performance  │
                       └─────────────────┘    └─────────────────┘
```

### **Callback Execution Timeline**

```
Timeline: ──────────────────────────────────────────────────────────▶

User Message
    │
    ▼
┌─────────────────┐
│ before_model    │ ← Records start time, model info
│ _callback       │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ LLM API Call    │ ← Actual request to Gemini
│ (Gemini 3 Flash)    │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ after_model     │ ← Calculates duration, tokens, cost
│ _callback       │
└─────────────────┘
    │
    ▼
Response to User
```

## 📖 Code Walkthrough

### **1. Callback Functions**

The callbacks work in pairs to monitor the complete LLM interaction:

**Before Callback (`before_model_callback`):**
- Extracts model information from `llm_request`
- Records request timestamp
- Stores data in session state for after callback
- Logs request details (model, time, agent)

**After Callback (`after_model_callback`):**
- Retrieves stored request data from session state
- Calculates response duration
- Extracts token usage from `llm_response.usage_metadata`
- Estimates API costs based on token count
- Logs performance metrics

### **2. State Management Between Callbacks**

```
Session State Flow:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ before_callback │───▶│  Session State  │───▶│ after_callback  │
│ stores:         │    │                 │    │ retrieves:      │
│ - start_time    │    │ - llm_request_  │    │ - start_time    │
│ - model         │    │   time          │    │ - model         │
│ - prompt_length │    │ - llm_model     │    │ - prompt_length │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **3. Agent Setup**

The agent is configured with both callbacks:
- `before_model_callback`: Monitors request initiation
- `after_model_callback`: Monitors response completion
- Uses `InMemoryRunner` for proper callback triggering

## 🧪 Testing Examples

### **Example Output Format**

```
🤖 LLM Request to gemini-3-flash-preview
⏰ Request time: 19:15:30
📋 Agent: llm_monitor_agent

📝 LLM Response from gemini-3-flash-preview
⏱️ Duration: 1.45s
🔢 Tokens: 156
💰 Estimated cost: $0.0004

```

### **What Each Metric Tells You**

- **⏰ Request time**: When the LLM request was initiated
- **⏱️ Duration**: Total time from request to response
- **🔢 Tokens**: Total tokens consumed (input + output)
- **💰 Estimated cost**: Approximate API cost based on token usage

## 🔍 Key Concepts

### **LLM Request Monitoring**
- **Model Information**: Track which model is being used
- **Timing**: Record request timestamps
- **State Management**: Store request data for response analysis

### **LLM Response Monitoring**
- **Response Time**: Calculate duration from request to response
- **Token Usage**: Track total tokens consumed
- **Cost Estimation**: Approximate API costs

### **Usage Metadata**
- **Token Count**: `llm_response.usage_metadata.total_token_count`
- **Model Information**: Available in request and response
- **Timing Data**: Stored in session state between callbacks

## 🎯 Use Cases

- **Performance Monitoring**: Track LLM response times
- **Cost Management**: Monitor API usage and costs
- **Quality Assurance**: Analyze prompt and response patterns
- **Debugging**: Troubleshoot LLM interaction issues
- **Analytics**: Collect usage statistics and metrics

## 🚨 Common Mistakes

1. **Incorrect callback signatures:**
   ```python
   # ❌ Wrong
   def before_model_callback(context, model, prompt):
   
   # ✅ Correct
   def before_model_callback(callback_context: CallbackContext, llm_request):
   ```

2. **Wrong token extraction:**
   ```python
   # ❌ Wrong
   tokens = llm_response.usage_metadata.get('total_token_count')
   
   # ✅ Correct
   tokens = getattr(llm_response.usage_metadata, 'total_token_count', 0)
   ```

3. **Not using InMemoryRunner:**
   ```python
   # ❌ Wrong - callbacks won't trigger
   agent.run(message)
   
   # ✅ Correct
   runner.run_async(...)
   ```

## 🔗 Next Steps

- Try Tutorial 6.3: Tool Execution Callbacks
- Experiment with different cost estimation models
- Add response quality metrics
- Implement rate limiting and quota management
- Create custom analytics dashboards 