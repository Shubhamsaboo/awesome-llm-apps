# 🏠 AI Real Estate Agent Team

The **AI Real Estate Agent Team** is a sophisticated property search and analysis platform powered by specialized AI agents with firecrawl's extract endpoint. This application provides comprehensive real estate insights, market analysis, and property recommendations using advanced web scraping and AI-powered search capabilities.

## Features

- **Multi-Agent Analysis System**
    - **Property Search Agent**: Finds properties using Firecrawl extract + Perplexity fallback
    - **Market Analysis Agent**: Provides elaborate market trends and neighborhood insights
    - **Property Valuation Agent**: Gives comprehensive property valuations and investment analysis

- **Multi-Platform Property Search**:
  - **Zillow**: Largest real estate marketplace with comprehensive listings
  - **Realtor.com**: Official site of the National Association of Realtors
  - **Trulia**: Neighborhood-focused real estate search
  - **Homes.com**: Comprehensive property search platform
  - **Perplexity AI**: AI-powered search across multiple sources as fallback

- **Advanced Property Analysis**:
  - Detailed property information extraction (address, price, bedrooms, bathrooms, sqft)
  - Property features and amenities analysis
  - Listing URLs and agent contact information
  - Clickable property links for easy navigation

- **Comprehensive Market Insights**:
  - Current market conditions (buyer's/seller's market)
  - Price trends over 6-12 months
  - Neighborhood analysis with school districts and safety ratings
  - Investment potential assessment with ROI projections
  - Comparative market analysis

- **Smart Fallback System**:
  - Primary: Firecrawl extract endpoint for structured data
  - Fallback: Google Search when extract returns no results
  - Seamless transition between data sources
  - Google Search indicator when using web search

- **Interactive UI Features**:
  - Real-time agent progression tracking
  - Progress indicators for each search phase
  - Downloadable analysis reports
  - Timing information for performance monitoring

## How to Run

Follow the steps below to set up and run the application:

### 1. **Get API Keys**:
   - **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
   - **Firecrawl API Key**: Get from [Firecrawl](https://firecrawl.dev)
   - **Google Search**: No API key required - uses Agno's GoogleSearchTools

### 2. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/awesome-llm-apps.git
   cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/ai_real_estate_agent_team
   ```

### 3. **Set Up Environment Variables**:
   Create a `.env` file in the project root and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   FIRECRAWL_API_KEY=your_firecrawl_api_key_here
   ```
   **Google Search is included automatically** - no API key required for fallback search functionality.

### 4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### 5. **Run the Streamlit App**:
   ```bash
   streamlit run real_estate_agent_team.py
   ```

## Usage Guide

### 1. **Configuration (Sidebar)**:
   - Enter your API keys (or use environment variables)
   - Select real estate websites to search
   - View the 3-agent workflow explanation

### 2. **Property Requirements**:
   - **Location**: City and state/province
   - **Budget**: Minimum and maximum price range
   - **Property Details**: Type, bedrooms, bathrooms, minimum square feet
   - **Special Features**: Parking, yard, view, proximity to amenities
   - **Timeline & Urgency**: How soon you need to move

### 3. **Analysis Process**:
   - **Search Phase**: Extracts property data from selected websites
   - **Agent Analysis**: Three specialized agents provide insights
   - **Results**: Comprehensive report with clickable property links

### 4. **Understanding Results**:
   - **Property Search Agent**: Lists found properties with details
   - **Market Analysis Agent**: Provides market trends and neighborhood insights
   - **Property Valuation Agent**: Gives investment analysis and valuations
   - **Property Links**: Clickable URLs to original listings

## Agent Workflow

### **Property Search Agent**
- Uses Firecrawl extract tools to search real estate websites
- Focuses on properties matching user criteria
- Falls back to Perplexity search if no properties found
- Organizes results with clickable listing URLs

### **Market Analysis Agent**
- **Market Trends**: Current conditions, price trends, inventory levels
- **Neighborhood Analysis**: Schools, safety, amenities, transportation
- **Investment Insights**: Potential assessment, rental data, development plans
- **Comparative Analysis**: Market comparisons and unique advantages

### **Property Valuation Agent**
- **Property Valuation**: Fair market value with detailed reasoning
- **Pricing Assessment**: Over/under-priced analysis with strategies
- **Investment Analysis**: ROI projections and risk assessment
- **Features Evaluation**: Detailed property analysis and improvements
- **Market Positioning**: Competitive analysis and target profiles

## Technical Architecture

### **Data Sources**:
- **Firecrawl Extract API**: Structured property data extraction
- **Perplexity AI**: AI-powered search across multiple sources
- **Pydantic Schemas**: Structured data validation and formatting

### **AI Framework**:
- **Agno Framework**: Multi-agent coordination and communication
- **OpenAI GPT-4**: Advanced language model for analysis
- **Streamlit**: Interactive web application interface

### **Performance Features**:
- **Rate Limiting**: Prevents API overload with intelligent delays
- **Progress Tracking**: Real-time updates on analysis progress
- **Timeout Handling**: Prevents hanging with 3-minute agent timeout
- **Error Recovery**: Graceful fallback when primary methods fail

## File Structure

```
ai_real_estate_agent_team/
├── real_estate_agent_team.py   # Main application file
├── requirements.txt            # Python dependencies
├── README.md                   # This documentation
└── .env                        # Environment variables (create this)
```

## API Requirements

### **OpenAI API**
- **Model**: GPT-4o
- **Usage**: Multi-agent analysis and property insights
- **Rate Limits**: Standard OpenAI rate limits apply

### **Firecrawl API**
- **Endpoint**: Extract API for structured data
- **Usage**: Property listing extraction from real estate websites
- **Rate Limits**: Firecrawl standard rate limits

### **Google Search**
- **Tool**: Agno GoogleSearchTools
- **Usage**: Web search for property listings fallback
- **Rate Limits**: Google Search standard rate limits

## Troubleshooting

### **Common Issues**:

1. **"No properties found"**:
   - This is normal for specific criteria
   - Perplexity fallback will provide market insights
   - Try broadening your search criteria

2. **API Key Errors**:
   - Ensure all API keys are valid and have sufficient credits
   - Check environment variables are properly set
   - Verify API key permissions

3. **Slow Performance**:
   - Reduce number of selected websites
   - Simplify property criteria
   - Check internet connection

4. **Agent Timeout**:
   - Simplify search criteria
   - Reduce number of websites
   - Try again with different parameters

### **Performance Tips**:
- Start with 1-2 websites for testing
- Use specific but not overly restrictive criteria
- Monitor timing information for optimization

