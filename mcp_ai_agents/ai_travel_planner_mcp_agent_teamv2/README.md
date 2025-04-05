
# 🧭 AI Travel Planning App (Multi-Agent System)

This project is a fully functional AI-powered travel planner built with [Agno](https://github.com/robinhad/agno) and [FastMCP](https://github.com/robinhad/fastmcp). It uses a multi-agent architecture to cover all aspects of trip planning—from finding places and accommodations to checking weather, reviews, and even blocking time in your Google Calendar.

---

## 🚀 Features

- 🗺️ **MapsAgent**  
  Get places, directions, and details using the Google Maps API.

- 🌦️ **WeatherAgent**  
  Fetch accurate weather forecasts and alerts using the National Weather Service.

- 🛏️ **BookingAgent**  
  Search accommodations using Booking.com or Airbnb (MCP tool-based integration).

- 🍽️ **ReviewsAgent**  
  Collect reviews and ratings from Yelp, TripAdvisor, and more.

- 📆 **CalendarAgent**  
  Automatically block travel dates and itinerary in Google Calendar.

- 🧠 **TeamLeaderAgent**  
  Central agent that coordinates all sub-agents to deliver unified trip plans.

---

## 🧱 Architecture

```
Streamlit App
     │
     ▼
TeamLeaderAgent (Agno)
     ├── MapsAgent (FastMCP)
     ├── WeatherAgent (FastMCP)
     ├── BookingAgent (FastMCP)
     ├── ReviewsAgent (FastMCP)
     └── CalendarAgent (FastMCP)
```

All agents are served as independent FastMCP servers using the `@mcp.tool()` API.

---

## 📦 Requirements

- Python 3.9+
- [Agno](https://pypi.org/project/agno/)
- [FastMCP](https://pypi.org/project/fastmcp/)
- Google Maps API Key
- OpenAI API Key
- Optional: API credentials for Booking.com, Yelp, TripAdvisor, and Google Calendar

---

## 🔧 Setup Instructions

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-username/mcp_multi_agents.git
   cd mcp_multi_agents
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**

   Create a `.env` file at the project root:

   ```env
   OPENAI_API_KEY=your-openai-api-key
   GOOGLE_MAPS_API_KEY=your-google-maps-api-key
   GOOGLE_CALENDAR_CLIENT_ID=your-client-id
   GOOGLE_CALENDAR_CLIENT_SECRET=your-client-secret
   ```

4. **Run Each MCP Server (in separate terminals or as background services)**

   ```bash
   python agents/maps.py
   python agents/weather.py
   python agents/booking.py
   python agents/reviews.py
   python agents/calendar.py
   ```

5. **Run the Streamlit App**

   ```bash
   streamlit run app.py
   ```

---

## 🧠 How It Works

- Each agent (Maps, Weather, Booking, Reviews, Calendar) provides tools via FastMCP.
- The `TeamLeaderAgent` queries all relevant agents and combines responses.
- The user interacts with a simple Streamlit interface.
- All API keys and tool usage are handled securely through environment variables.

---

## 📁 Project Structure

```
mcp_multi_agents/
├── agents/
│   ├── team.py               # TeamLeaderAgent and multi-agent configuration
│   ├── maps.py               # Google Maps tools (places, directions)
│   ├── weather.py            # Weather forecasts and alerts
│   ├── booking.py            # Accommodation search
│   ├── reviews.py            # Yelp & TripAdvisor reviews
│   └── calendar.py           # Google Calendar scheduling
├── app.py                    # Streamlit frontend
├── main.py                   # CLI entry (optional)
├── requirements.txt
└── .env                      # Secrets and API keys
```

---

## 📌 Next Steps

- [ ] PDF trip summary export
- [ ] User authentication + trip history
- [ ] Voice assistant integration
- [ ] More itinerary control (multi-day, by interest)

---

## 💬 Need Help?

Feel free to open an issue, submit a PR, or ping the team for support on specific APIs or agent configurations!

---

## 🤝 Credits

- [Agno](https://github.com/robinhad/agno) – Agent architecture
- [FastMCP](https://github.com/robinhad/fastmcp) – Tool routing
- [Streamlit](https://streamlit.io/) – User interface
- [Google APIs](https://developers.google.com/)
- [OpenAI](https://openai.com/)
