## 🔍 AI Fraud Investigation Agent

An AI-powered autonomous fraud investigation agent that cross-references childcare provider licensing records against physical building data to detect anomalies. The agent uses public data — Cook County property records, Illinois DCFS licensing, Google Maps, and the Secretary of State — to find facilities where the physical evidence doesn't match the paperwork.

### Features

- Searches Illinois DCFS licensing database for providers by ZIP code
- Cross-references licensed capacity against actual building square footage from Cook County GIS records
- Applies IL building code math to calculate maximum legal childcare occupancy
- Analyzes Google Street View imagery to verify a facility looks like a real childcare center
- Checks Google Places for business status, rating, and whether the address shows a different business entirely
- Verifies business entity registration with the Illinois Secretary of State
- Discovers cross-provider patterns: shared owners, address clusters, entities with no public footprint
- Narrates its full investigation in real time — reasoning is visible as the agent works

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/single_agent_apps/ai_fraud_investigation_agent
```

2. Install the required dependencies

```bash
pip install -r requirements.txt
```

3. Get your OpenRouter API Key

- Sign up at [openrouter.ai](https://openrouter.ai) and create an API key
- The free tier is sufficient for demo investigations
- Default model: `anthropic/claude-sonnet-4.6`

4. Get your Google Maps API Key *(optional — skips visual analysis if omitted)*

- Create a project at [console.cloud.google.com](https://console.cloud.google.com)
- Enable: **Geocoding API**, **Places API**, **Street View Static API**
- Create an API key and restrict it to these three APIs

5. Run the Streamlit App

```bash
streamlit run fraud_investigation_agent.py
```

### How it Works?

The AI Fraud Investigation Agent uses 7 specialized tools, all powered by public data sources:

- **Provider Search** — Queries the Illinois DCFS licensing portal for all active providers in a ZIP code, returning capacity, license type, and license status

- **Property Analysis** — Pulls building square footage, lot size, property class, and year built from the Cook County Assessor's open data (Socrata API, no auth required)

- **Capacity Calculation** — Applies Illinois DCFS Part 407 building code math: `(building_sqft × 0.65) ÷ 35 = max legal children`. A 900 sq ft building cannot legally serve 50 children — this is a mathematical impossibility, not an opinion

- **Street View** — Captures four-directional Google Street View images to check whether the address looks like a real childcare facility or something else entirely

- **Places Info** — Queries Google Places for the current business listed at the address, its operating status, rating, and recent reviews

- **Business Registration** — Probes the Illinois Secretary of State to verify the provider is a registered legal entity

- **Geocoding** — Converts addresses to coordinates for spatial analysis

The agent investigates each provider in the ZIP code, narrating its reasoning as it works. When it notices something suspicious — a building too small for its license, a closed storefront claiming to run childcare, a name appearing across multiple providers — it follows that thread and explains why it matters.

### What the Agent Can (and Cannot) Detect

**Can detect:**
- Licensed capacity physically impossible for the building size
- Addresses where Google shows a different business or a closed/vacant building
- Providers with no Google listing, no reviews, no business registration
- Shared owner names or agents appearing across multiple providers

**Cannot detect:**
- Attendance fraud (billing for children who didn't show up) — requires non-public CCAP billing records
- Any fraud requiring access to internal DHS or county billing data

All findings are investigative leads, not legal conclusions. The agent uses language like "requires further investigation" and "exhibits anomalies" — never "fraud."

### Geographic Scope

This demo covers **Cook County, Illinois only**. Property data is sourced from the Cook County Assessor's open data, so the ZIP code selector is limited to 10 high-density Chicago neighborhoods known for concentrations of subsidized childcare providers:

| ZIP | Neighborhood |
|-----|-------------|
| 60623 | Little Village / North Lawndale |
| 60629 | Chicago Lawn |
| 60644 | Austin |
| 60621 | Englewood |
| 60628 | Roseland |
| 60619 | Chatham / Auburn Gresham |
| 60636 | West Englewood |
| 60612 | Near West Side |
| 60620 | Auburn Gresham |
| 60624 | Garfield Park |

The full [Surelock Homes](https://github.com/oso95/Surelock-Homes) system supports Minnesota and additional Illinois counties with a FastAPI backend, streaming dashboard, and offline mode.
