# 🍽️ AI Recipe & Meal Planning Agent

An intelligent meal planning agent built with Agno that helps you discover recipes, analyze nutrition, estimate costs, and create weekly meal plans based on your ingredients and dietary preferences.

## Features

🔍 **Recipe Discovery**
- Find recipes based on available ingredients
- Support for dietary restrictions (vegetarian, vegan, keto, paleo, etc.)
- Ingredient substitution suggestions
- Detailed cooking instructions and timing

📊 **Nutrition Analysis**
- Comprehensive nutritional breakdown per serving
- User-friendly health assessments
- Calorie, protein, carb, and fat tracking
- Sodium and fiber content analysis

💰 **Cost Estimation**
- Grocery cost estimation for ingredients
- Budget-friendly meal suggestions
- Cost per serving calculations

📅 **Weekly Meal Planning**
- Balanced meal plans for any household size
- Dietary preference accommodation
- Shopping list optimization
- Budget-conscious planning

🧠 **Session-Based Conversations**
- Remembers context during your current browser session
- Preferences are not persisted after restart (no long-term storage)

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/single_agent_apps/ai_recipe_meal_planning_agent
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Get your OpenAI API Key

- Sign up for an [OpenAI account](https://platform.openai.com/) and obtain your API key.

4. Get your Spoonacular API Key

- Sign up for a [Spoonacular account](https://spoonacular.com/food-api) and obtain your API key (free tier ~50 requests/day).

5. Create a `.env` file in this folder

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional but recommended for full recipe & nutrition functionality
SPOONACULAR_API_KEY=your_spoonacular_api_key_here
```

6. Run the Streamlit App

```bash
streamlit run ai_recipe_meal_planning_agent.py
```

7. Open your browser at `http://localhost:8501`

## Example Interactions

**Recipe Discovery:**
- "I have chicken, broccoli, and rice. What can I make?"
- "Find me vegan recipes using lentils"
- "Show me quick 30-minute dinner ideas"

**Nutrition Analysis:**
- "What's the nutritional content of this recipe?"
- "Is this meal high in protein?"
- "How many calories per serving?"

**Meal Planning:**
- "Create a week's worth of vegetarian meals for 2 people"
- "I need a low-sodium meal plan"
- "Plan budget-friendly meals for a family of 4"

**Cost Estimation:**
- "How much will these ingredients cost?"
- "What's the most budget-friendly option?"
- "Estimate weekly grocery costs for this meal plan"

## Application Architecture

### Built with Agno Framework
- **Agent**: OpenAI GPT-5 mini powered meal planning agent
- **Memory**: Conversation memory for personalized recommendations
- **Tools**: Custom tools for recipe search and analysis + DuckDuckGo web search
- **Interface**: Streamlit web application

### Custom Tools
1. `search_recipes(ingredients, diet_type=None)` - Recipe discovery via Spoonacular API with detailed instructions
2. `analyze_nutrition(recipe_name)` - Detailed nutritional analysis via Spoonacular
3. `estimate_costs(ingredients, servings=4)` - Budget planning and cost estimation
4. `create_meal_plan(dietary_preference="balanced", people=2, days=7, budget="moderate")` - Comprehensive weekly meal planning with shopping list
5. `DuckDuckGoTools` - Web search for additional context

### Key Technologies
- **Agno**: AI agent framework
- **Streamlit**: Web interface and user interaction
- **Spoonacular API**: Recipe and nutrition data
- **OpenAI GPT-5 mini**: Natural language understanding and generation

## Customization

### Adding New Dietary Preferences
Modify the `search_recipes` tool to include additional diet types supported by Spoonacular API.

### Extending Cost Database
Update the `ingredient_costs` dictionary in `estimate_grocery_costs()` with local pricing.

### Custom Meal Categories
Edit the `meal_categories` in `create_weekly_meal_plan()` to match your preferences.

## Troubleshooting

**API Key Issues:**
- Ensure your `.env` file is in the correct directory
- Verify API keys are valid and have sufficient credits
- Check API key format (no extra spaces or quotes)
 - Note: Without `SPOONACULAR_API_KEY`, recipe search and nutrition tools will return an error; other features will still load.

**Recipe Search Not Working:**
- Verify Spoonacular API key is set correctly
- Check your API usage limits (150 requests/day for free tier)
- Try simpler ingredient searches

**Memory Issues:**
- The agent uses conversation memory to remember preferences
- Clear browser cache if experiencing persistent issues
- Restart the application to reset conversation history

## Contributing

Feel free to contribute by:
- Adding new recipe sources or APIs
- Improving nutrition analysis algorithms
- Enhancing cost estimation accuracy
- Adding new meal planning features

## License

This project is open source. Please check the main repository for license details.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the Agno documentation
- Open an issue in the main repository
