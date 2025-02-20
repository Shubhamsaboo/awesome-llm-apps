# 🌍 AQI Analysis Agent

The AQI Analysis Agent is a powerful air quality monitoring and health recommendation tool powered by Firecrawl and Agno's AI Agent framework. This app helps users make informed decisions about outdoor activities by analyzing real-time air quality data and providing personalized health recommendations.

## Features

- **Multi-Agent System**
    - **AQI Analyzer**: Fetches and processes real-time air quality data
    - **Health Recommendation Agent**: Generates personalized health advice

- **Air Quality Metrics**:
  - Overall Air Quality Index (AQI)
  - Particulate Matter (PM2.5 and PM10)
  - Carbon Monoxide (CO) levels
  - Temperature
  - Humidity
  - Wind Speed

- **Comprehensive Analysis**:
  - Real-time data visualization
  - Health impact assessment
  - Activity safety recommendations
  - Best time suggestions for outdoor activities
  - Weather condition correlations

- **Interactive Features**:
  - Location-based analysis
  - Medical condition considerations
  - Activity-specific recommendations
  - Downloadable reports
  - Example queries for quick testing

## How to Run

Follow these steps to set up and run the application:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials/ai_aqi_analysis_agent
   ```

2. **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up your API keys**:
    - Get an OpenAI API key from: https://platform.openai.com/api-keys
    - Get a Firecrawl API key from: [Firecrawl website](https://www.firecrawl.dev/app/api-keys)

4. **Run the Gradio app**:
    ```bash
    python ai_aqi_analysis_agent.py
    ```

5. **Access the Web Interface**:
    - The terminal will display two URLs:
      - Local URL: `http://127.0.0.1:7860` (for local access)
      - Public URL: `https://xxx-xxx-xxx.gradio.live` (for temporary public access)
    - Click on either URL to open the web interface in your browser

## Usage

1. Enter your API keys in the API Configuration section
2. Input location details:
   - City name
   - State (optional for Union Territories/US cities)
   - Country
3. Provide personal information:
   - Medical conditions (optional)
   - Planned outdoor activity
4. Click "Analyze & Get Recommendations" to receive:
   - Current air quality data
   - Health impact analysis
   - Activity safety recommendations
5. Try the example queries for quick testing

## Note

The air quality data is fetched using Firecrawl's web scraping capabilities. Due to caching and rate limiting, the data might not always match real-time values on the website. For the most accurate real-time data, consider checking the source website directly.
