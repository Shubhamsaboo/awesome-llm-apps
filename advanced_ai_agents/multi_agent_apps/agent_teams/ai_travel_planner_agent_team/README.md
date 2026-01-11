# ✈️ TripCraft AI

**Your journey, perfectly crafted with intelligence.**

Travel planning is overwhelming—juggling dozens of tabs, comparing conflicting info, spending hours just to get started. TripCraft AI makes that disappear. It's a multi-agent AI system that turns simple inputs into complete travel itineraries. Describe your ideal trip, and it handles flights, hotels, activities, and budget automatically.

## 🎯 Goal

Make travel planning effortless and personal. No stress, no endless research—just a plan that feels crafted specifically for you.

---

## 🚀 Quick Start Guide

### Prerequisites

- **Node.js** 20.x or higher
- **Python** 3.12 or higher
- **PostgreSQL** database
- **pnpm** 9.15.0 or higher (for frontend)
- **uv** (for Python backend) or pip

### Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team
```

#### 2. Setup Frontend (Client)

```bash
cd client

# Install pnpm if not already installed
npm install -g pnpm@9.15.0

# Install dependencies
pnpm install

# Create environment file
cp .env.example .env.local

# Edit .env.local with your configuration
# Required variables:
# - NEXT_PUBLIC_BASE_URL=http://localhost:3000
# - DATABASE_URL=postgresql://user:password@localhost:5432/tripcraft
# - NEXT_PUBLIC_API_URL=http://localhost:8000

# Setup database
pnpm prisma generate
pnpm prisma migrate dev

# Run development server
pnpm dev
```

The frontend will be available at [http://localhost:3000](http://localhost:3000)

#### 3. Setup Backend

```bash
cd backend

# Create environment file
cp .env.example .env

# Edit .env with your API keys:
# - DATABASE_URL (PostgreSQL connection string)
# - EXA_API_KEY (for search)
# - FIRECRAWL_API_KEY (for web scraping)
# - OPENAI_API_KEY or OPENROUTER_API_KEY (for LLM)
# - BRIGHT_DATA credentials (for browser automation)
# - CLOUDFLARE R2 credentials (for storage)

# Install dependencies using uv (recommended)
uv sync

# Or using pip
pip install -e .

# Run the backend server
python main.py
```

The backend API will be available at [http://localhost:8000](http://localhost:8000)

### Common Setup Issues

#### Issue: "TypeError: Failed to parse URL from undefined/api/auth/get-session"

**Solution**: Set `NEXT_PUBLIC_BASE_URL=http://localhost:3000` in your `.env.local` file.

#### Issue: Database connection errors

**Solution**: 
1. Ensure PostgreSQL is running
2. Verify your `DATABASE_URL` is correct in both client and backend `.env` files
3. Run `pnpm prisma migrate dev` in the client directory

#### Issue: ESLint errors in generated files

**Solution**: The generated Prisma files are now ignored by ESLint. Run `pnpm lint` to verify.

---

## ⚙️ How It Works

1. **🎯 Input Your Vision** - Fill out a form with destination, dates, budget, travel style, and preferences
2. **🤖 AI Agents Collaborate** - Specialized agents handle flights, hotels, activities, and budgeting in parallel
3. **🗺️ Get Your Itinerary** - Receive a complete day-by-day plan with bookings, costs, and recommendations

### Key Features
- **Personalized Planning** - Tailored to your travel style and interests
- **Hidden Gems Discovery** - Beyond typical tourist spots using advanced search
- **Smart Optimization** - Balances cost, time, and experience
- **Complete Packages** - Everything from flights to dining recommendations

---

## 🛠️ Tech Stack

**Frontend:** Next.js 15.3.3, React 19, TypeScript
**Backend:** Python 3.12+, FastAPI, PostgreSQL
**AI:** Agno (agent coordination), Gemini (LLM), Exa (search), Firecrawl (web scraping)
**APIs:** Google Flights, Kayak
**Auth:** Better-auth
**ORM:** Prisma

---

## 📸 Visuals

![Image](https://github.com/user-attachments/assets/5fae2938-6d2c-4fc7-86be-d22bb84729a6)
![Image](https://github.com/user-attachments/assets/1bd6e98f-ae32-47be-90a0-23ee6f06c613)
![Image](https://github.com/user-attachments/assets/45db7d19-67ca-4c92-985f-79a7cb976b1c)
![Image](https://github.com/user-attachments/assets/7a06c3de-281d-4820-a517-ea81137289d7)
![Image](https://github.com/user-attachments/assets/523f0d02-8a72-4709-b3d4-5102f1d1b950)
![Image](https://github.com/user-attachments/assets/dbab944a-7678-4eae-9ead-05f15c3de407)

---

## 👥 About

**Built by**: Amit Wani [@mtwn105](https://github.com/mtwn105)

Full-stack developer and software engineer passionate about building intelligent systems that solve real-world problems. TripCraft AI represents the intersection of advanced AI capabilities and practical travel planning needs.

---

## 🎬 Demo Video Link

[https://youtu.be/eTll7EdQyY8](https://youtu.be/eTll7EdQyY8)

---

## 🤖 AI Agents

Six specialized agents work together to create comprehensive travel plans:

1. **🏛️ Destination Explorer** - Researches attractions, landmarks, and experiences
2. **🏨 Hotel Search Agent** - Finds accommodations based on location, budget, and amenities
3. **🍽️ Dining Agent** - Recommends restaurants and culinary experiences
4. **💰 Budget Agent** - Handles cost optimization and financial planning
5. **✈️ Flight Search Agent** - Plans air travel routes and comparisons
6. **📅 Itinerary Specialist** - Creates detailed day-by-day schedules with optimal timing
