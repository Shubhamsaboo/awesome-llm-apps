## 🧵 Strands Starter Agent

A single-file agent built with the Strands Agents SDK, running on an OpenAI model. It shows the smallest useful Strands setup: define tools with the `@tool` decorator, hand them to an `Agent`, and let the model decide when to call them. This is a good starting point for building your own Strands agents.

The example agent analyzes text with two tools, `word_count` and `character_count`.

### Features
- **Tool calling with Strands**: Two custom tools defined with the `@tool` decorator
- **Model-driven tool use**: The agent picks the right tool based on your prompt
- **Runs with one key**: Only an OpenAI API key is needed
- **Streamlit UI**: Enter a prompt and see the response

### How to Get Started
1. **Clone the repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/starter_ai_agents/strands_starter_agent
   ```

2. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**:
   ```bash
   streamlit run strands_starter_agent.py
   ```

4. **Use the app**:
   - Enter your OpenAI API key in the sidebar
   - Pick a model
   - Type a prompt and click Run

### How it works
1. Two functions are marked as tools with the Strands `@tool` decorator.
2. A Strands `Agent` is created with an OpenAI model and those tools.
3. When you send a prompt, the model decides whether to call a tool and writes the answer.

### Example prompts
- How many words are in: the quick brown fox jumps over the lazy dog?
- Count the characters in 'hello world' without spaces.
- Give me both the word count and character count of this sentence.

### References
- [Strands Agents documentation](https://strandsagents.com)
- [OpenAI model provider in Strands](https://strandsagents.com/docs/user-guide/concepts/model-providers/openai/)
