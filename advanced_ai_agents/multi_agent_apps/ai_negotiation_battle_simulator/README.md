# 🎮 AI Negotiation Battle Simulator

### A Real-Time Agent vs Agent Showdown!

Watch two AI agents battle it out in an epic used car negotiation! One agent desperately wants that sweet 2019 Honda Civic, the other is determined to squeeze every last dollar. Who will crack first? 🚗💰

## ✨ Features

- **🤖 Dual AI Agents**: Buyer vs Seller with distinct personalities and strategies
- **🔄 A2A Protocol Ready**: Demonstrates Google's Agent-to-Agent protocol for cross-agent communication
- **📊 Live Negotiation Tracking**: Watch offers, counteroffers, and dramatic moments unfold
- **🎭 Configurable Personalities**: From "Desperate First-Time Buyer" to "Ruthless Used Car Dealer"
- **🎬 Dramatic Scenarios**: Pre-built scenarios with backstories and stakes

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                 Streamlit UI                     │
│    Buyer Panel  │  Timeline  │  Seller Panel    │
└────────┬────────────────────────────┬───────────┘
         │                            │
         ▼                            ▼
┌─────────────────┐          ┌─────────────────┐
│   Buyer Agent   │◄────────►│  Seller Agent   │
│   (Google ADK)  │  A2A/    │  (Google ADK)   │
│                 │  Direct  │                 │
│ • Budget: $12k  │          │ • Min: $14k     │
│ • Strategy: 🎯  │          │ • Strategy: 💰  │
└─────────────────┘          └─────────────────┘
         │                            │
         └──────────┬─────────────────┘
                    ▼
         ┌─────────────────┐
         │   Orchestrator  │
         │  (Manages Flow) │
         └─────────────────┘
```

## 🚀 Quick Start

### 1. Clone and Navigate
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/multi_agent_apps/ai_negotiation_battle_simulator
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment
Create a `.env` file:
```bash
GOOGLE_API_KEY=your_google_ai_studio_key_here
```

Get your API key from [Google AI Studio](https://aistudio.google.com/)

### 4. Run the Battle!
```bash
streamlit run negotiation_app.py
```

## 🎭 The Scenario: "The Craigslist Showdown"

**THE CAR**: 2019 Honda Civic EX, 45,000 miles, one owner, minor scratch on bumper

**THE BUYER** 🎯: 
- Recently graduated, needs reliable car for new job
- Has exactly $12,500 saved (with $500 emergency buffer)
- Found 3 similar cars online priced $13,000-$16,000
- *Secret*: Job starts Monday. Desperately needs a car.

**THE SELLER** 💰:
- Upgrading to an SUV, needs to sell the Civic first
- Paid $22,000 new, KBB says $14,500 private party
- Has one other interested buyer coming tomorrow
- *Secret*: The other buyer is flaky and might not show.

**THE STAKES**: Both have secrets. Both have pressure. Only one deal can be made.

## ⚙️ Configuration Options

### Negotiation Settings

| Setting | Options | Description |
|---------|---------|-------------|
| **Buyer Strategy** | Aggressive, Balanced, Patient | How pushy the buyer is |
| **Seller Strategy** | Firm, Flexible, Desperate | How willing to negotiate |
| **Max Rounds** | 3-15 | How many back-and-forths before walkaway |
| **Initial Offer** | % of asking | Where buyer starts |
| **Drama Level** | 🎭 to 🎭🎭🎭 | How theatrical the agents get |

### Preset Personalities

**Buyers:**
- 😰 *Desperate Dan* - Needs car TODAY, weak poker face
- 🧮 *Analytical Alex* - Cites every data point, very logical  
- 😎 *Cool-Hand Casey* - Master of the walkaway bluff
- 🤝 *Fair-Deal Fran* - Just wants a win-win

**Sellers:**
- 🦈 *Shark Steve* - Never drops more than 5%, take it or leave it
- 📊 *By-The-Book Beth* - Goes strictly by KBB, reasonable but firm
- 😅 *Motivated Mike* - Really needs to sell, more flexible
- 🎭 *Drama Queen Diana* - Everything is "my final offer" (it's not)

## 📁 Project Structure

```
ai_negotiation_battle_simulator/
├── README.md               # This file
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
├── negotiation_app.py     # Main Streamlit application
├── agents/
│   ├── __init__.py
│   ├── buyer_agent.py     # Buyer agent with negotiation tools
│   ├── seller_agent.py    # Seller agent with pricing tools
│   └── orchestrator.py    # Manages negotiation flow
├── config/
│   ├── __init__.py
│   ├── personalities.py   # Agent personality presets
│   └── scenarios.py       # Negotiation scenarios
└── utils/
    ├── __init__.py
    └── negotiation_state.py  # State management
```

## 🔄 A2A Protocol Mode (Advanced)

For true cross-process agent communication, you can run agents as separate A2A servers:

### Terminal 1: Start Seller Agent
```bash
python -m agents.seller_agent --port 8001
```

### Terminal 2: Start Buyer Agent  
```bash
python -m agents.buyer_agent --port 8002
```

### Terminal 3: Run Orchestrator
```bash
python -m agents.orchestrator --buyer-url http://localhost:8002 --seller-url http://localhost:8001
```

## 🎬 Sample Negotiation

```
🚗 NEGOTIATION BEGINS: 2019 Honda Civic EX

📋 ASKING PRICE: $15,500

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 BUYER (Round 1):
"I've done my research - KBB shows similar Civics at $13,500. 
Given the scratch on the bumper and the 45k miles, I'm prepared 
to offer $11,500 cash today."

💰 SELLER (Round 1):
"I appreciate the offer, but this Civic has been meticulously 
maintained. Single owner, all service records. That KBB price 
is for good condition - this is excellent. I could come down 
to $15,000."

🎯 BUYER (Round 2):
"Look, I can see it's been well cared for, and I want to make 
this work. But $15k is still above market. I can stretch to 
$12,500 - that's my absolute max as a recent grad."

💰 SELLER (Round 2):
*pauses* "I've got another buyer coming tomorrow who seemed 
very interested... but I'd rather close this today. $14,000 
and it's yours."

🎯 BUYER (Round 3):
"I hear you on the other buyer. Let me be straight with you - 
I start a new job Monday and I really need reliable transport. 
$13,000 and I'll throw in taking it as-is, no inspection."

💰 SELLER (Round 3):
*considers* "You seem like someone who'll take care of her. 
$13,500, I'll include the winter floor mats I was going to keep, 
and we have a deal."

🎯 BUYER (Round 4):
"$13,250 - right in the middle. Final offer. I've got cash ready."

💰 SELLER (Round 4):
"...You drive a hard bargain. Deal. 🤝"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DEAL CLOSED AT $13,250

📊 RESULTS:
• Buyer saved: $2,250 (14.5% off asking)
• Seller achieved: $13,250 (91% of asking, above KBB)
• Rounds: 4
• Winner: BOTH (True win-win! 🎉)
```

## 🧠 How It Works

1. **Scenario Loading**: The negotiation context (car details, buyer/seller situations) is loaded
2. **Agent Initialization**: Both agents receive their private information and strategies
3. **Turn-Based Negotiation**: 
   - Buyer makes offer with reasoning
   - Seller evaluates and responds
   - Process repeats until deal or walkaway
4. **State Tracking**: All offers, counteroffers, and reasoning are logged
5. **Outcome Determination**: Deal, walkaway, or max rounds reached

## 🤝 Contributing

Feel free to add:
- New negotiation scenarios (salary, apartment, contracts)
- Additional personality types
- Enhanced UI visualizations
- Cross-framework agent support (LangChain, CrewAI)

## 📚 Learn More

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [A2A Protocol Specification](https://a2a-protocol.org/)
- [AG-UI Protocol](https://docs.ag-ui.com/)

---

*May the best negotiator win!* 🏆
