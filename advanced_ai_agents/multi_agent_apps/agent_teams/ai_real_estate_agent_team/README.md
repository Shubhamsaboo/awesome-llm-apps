# 🏠 AI Real Estate Agent Team

The **AI Real Estate Agent Team** is a sophisticated property search and analysis platform powered by specialized AI agents with Firecrawl's extract endpoint. This application provides comprehensive real estate insights, market analysis, and property recommendations using advanced web scraping and AI-powered search capabilities.

## Features

- **Multi-Agent Analysis System**
    - **Property Search Agent**: Finds properties using direct Firecrawl integration
    - **Market Analysis Agent**: Provides concise market trends and neighborhood insights
    - **Property Valuation Agent**: Gives brief property valuations and investment analysis

- **Multi-Platform Property Search**:
  - **Zillow**: Largest real estate marketplace with comprehensive listings
  - **Realtor.com**: Official site of the National Association of Realtors
  - **Trulia**: Neighborhood-focused real estate search
  - **Homes.com**: Comprehensive property search platform

- **Advanced Property Analysis**:
  - Detailed property information extraction (address, price, bedrooms, bathrooms, sqft)
  - Property features and amenities analysis
  - Listing URLs and agent contact information
  - Clickable property links for easy navigation

- **Comprehensive Market Insights**:
  - Current market conditions (buyer's/seller's market)
  - Price trends and market direction
  - Neighborhood analysis with key insights
  - Investment potential assessment
  - Strategic recommendations

- **Sequential Manual Execution**:
  - Optimized for speed and reliability
  - Direct data flow between agents
  - Manual coordination for better control
  - Reduced overhead and improved performance

- **Interactive UI Features**:
  - Real-time agent progression tracking
  - Progress indicators for each search phase
  - Downloadable analysis reports
  - Timing information for performance monitoring

## Requirements

The application requires the following Python libraries:

- `agno`
- `streamlit`
- `firecrawl-py`
- `python-dotenv`
- `pydantic`

You'll also need API keys for:
- **Cloud Version**: Google AI (Gemini) + Firecrawl
- **Local Version**: Firecrawl only (uses Ollama locally)

## How to Run

Follow these steps to set up and run the application:

### **API Version (Gemini 2.5 Flash)**

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_real_estate_agent_team
   ```

2. **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up your API keys**:
    - Get a Google AI API key from: https://aistudio.google.com/app/apikey
    - Get a Firecrawl API key from: [Firecrawl website](https://firecrawl.dev)

4. **Run the Streamlit app**:
    ```bash
    streamlit run real_estate_agent_team.py
    ```

### **Local Version (Ollama)**

1. **Install Ollama**:
   ```bash
   #Pull the model: make sure to have a device that has more than 16GB RAM to run this model locally!
   ollama pull gpt-oss:20b  
   ```

2. **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up your API key**:
    - Get a Firecrawl API key from: [Firecrawl website](https://firecrawl.dev)

4. **Run the local Streamlit app**:
    ```bash
    streamlit run local_ai_real_estate_agent_team.py
    ```

## Usage

### **Cloud Version**

1. Enter your API keys in the sidebar:
   - Google AI API Key
   - Firecrawl API Key

2. Select real estate websites to search from:
   - Zillow
   - Realtor.com
   - Trulia
   - Homes.com

3. Configure your property requirements:
   - Location (city, state)
   - Budget range
   - Property details (type, bedrooms, bathrooms, sqft)
   - Special features and timeline

4. Click "Start Property Analysis" to generate:
   - Property listings with details
   - Market analysis and trends
   - Property valuations and recommendations

### **Local Version**

1. Enter your Firecrawl API key in the sidebar
2. Ensure Ollama is running with `gpt-oss:20b` model
3. Follow the same property configuration steps as cloud version
4. Get the same comprehensive analysis with local AI processing

## Agent Workflow

### **Property Search Agent**
- Uses direct Firecrawl integration to search real estate websites
- Focuses on properties matching user criteria
- Extracts structured property data with all details
- Organizes results with clickable listing URLs

### **Market Analysis Agent**
- **Market Condition**: Buyer's/seller's market, price trends
- **Key Neighborhoods**: Brief overview of areas where properties are located
- **Investment Outlook**: 2-3 key points about investment potential
- **Format**: Concise bullet points under 100 words per section

### **Property Valuation Agent**
- **Value Assessment**: Fair price, over/under priced analysis
- **Investment Potential**: High/Medium/Low with brief reasoning
- **Key Recommendation**: One actionable insight per property
- **Format**: Brief assessments under 50 words per property

## Technical Architecture

### **Data Sources**:
- **Firecrawl Extract API**: Structured property data extraction
- **Pydantic Schemas**: Structured data validation and formatting

### **AI Framework**:
- **Cloud Version**: Agno Framework with Google Gemini 2.5 Flash
- **Local Version**: Agno Framework with Ollama gpt-oss:20b
- **Streamlit**: Interactive web application interface

### **Performance Features**:
- **Sequential Execution**: Manual coordination for optimal performance
- **Progress Tracking**: Real-time updates on analysis progress
- **Error Recovery**: Graceful handling of extraction failures
- **Direct Integration**: Bypasses tool wrappers for faster execution

## File Structure

```
ai_real_estate_agent_team/
├── real_estate_agent_team.py           # API version (Google Gemini)
├── local_ai_real_estate_agent_team.py  # Local version (Ollama)
├── requirements.txt                    # Python dependencies
├── README.md                          # This documentation
└── .env                               # Environment variables (create this)
```

## API Requirements

### **Cloud Version**

#### **Google AI API**
- **Model**: Gemini 2.5 Flash
- **Usage**: Multi-agent analysis and property insights
- **Rate Limits**: Standard Google AI rate limits apply

#### **Firecrawl API**
- **Endpoint**: Extract API for structured data
- **Usage**: Property listing extraction from real estate websites
- **Rate Limits**: Firecrawl standard rate limits

### **Local Version**

#### **Firecrawl API**
- **Endpoint**: Extract API for structured data
- **Usage**: Property listing extraction from real estate websites
- **Rate Limits**: Firecrawl standard rate limits

#### **Ollama (Local)**
- **Model**: gpt-oss:20b
- **Usage**: All AI processing locally
- **Requirements**: ~16GB RAM recommended
- **No API costs**: Completely local processing


