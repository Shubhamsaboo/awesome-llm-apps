import asyncio
import os
import streamlit as st
import random
from textwrap import dedent
from typing import Dict, List, Optional

from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.openai import OpenAIChat
from agno.tools import tool
import requests
from dotenv import load_dotenv
from agno.tools.duckduckgo import DuckDuckGoTools   

load_dotenv()

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@tool
def search_recipes(ingredients: str, diet_type: Optional[str] = None) -> Dict:
    """Search for detailed recipes with cooking instructions."""
    if not SPOONACULAR_API_KEY:
        return {"error": "Spoonacular API key not found"}
    
    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "ingredients": ingredients,
        "number": 5,
        "ranking": 2,
        "ignorePantry": True
    }
    if diet_type:
        params["diet"] = diet_type
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        recipes = response.json()
        
        detailed_recipes = []
        for recipe in recipes[:3]:
            detail_url = f"https://api.spoonacular.com/recipes/{recipe['id']}/information"
            detail_response = requests.get(detail_url, params={"apiKey": SPOONACULAR_API_KEY}, timeout=10)
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                detailed_recipes.append({
                    "id": recipe['id'],
                    "title": recipe['title'],
                    "ready_in_minutes": detail_data.get('readyInMinutes', 'N/A'),
                    "servings": detail_data.get('servings', 'N/A'),
                    "health_score": detail_data.get('healthScore', 0),
                    "used_ingredients": [i['name'] for i in recipe['usedIngredients']],
                    "missing_ingredients": [i['name'] for i in recipe['missedIngredients']],
                    "instructions": detail_data.get('instructions', 'Instructions not available')
                })
        
        return {
            "recipes": detailed_recipes,
            "total_found": len(recipes)
        }
    except:
        return {"error": "Recipe search failed"}

@tool
def analyze_nutrition(recipe_name: str) -> Dict:
    """Get nutrition analysis for a recipe by searching for it."""
    if not SPOONACULAR_API_KEY:
        return {"error": "API key not found"}
    
    # First search for the recipe
    search_url = "https://api.spoonacular.com/recipes/complexSearch"
    search_params = {
        "apiKey": SPOONACULAR_API_KEY,
        "query": recipe_name,
        "number": 1,
        "addRecipeInformation": True,
        "addRecipeNutrition": True
    }
    
    try:
        search_response = requests.get(search_url, params=search_params, timeout=15)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        if not search_data.get('results'):
            return {"error": f"No recipe found for '{recipe_name}'"}
        
        recipe = search_data['results'][0]
        
        if 'nutrition' not in recipe:
            return {"error": "No nutrition data available for this recipe"}
        
        nutrients = {n['name']: n['amount'] for n in recipe['nutrition']['nutrients']}
        calories = round(nutrients.get('Calories', 0))
        protein = round(nutrients.get('Protein', 0), 1)
        carbs = round(nutrients.get('Carbohydrates', 0), 1)
        fat = round(nutrients.get('Fat', 0), 1)
        fiber = round(nutrients.get('Fiber', 0), 1)
        sodium = round(nutrients.get('Sodium', 0), 1)
        
        # Health insights
        health_insights = []
        if protein > 25:
            health_insights.append("✅ High protein - great for muscle building")
        if fiber > 5:
            health_insights.append("✅ High fiber - supports digestive health")
        if sodium < 600:
            health_insights.append("✅ Low sodium - heart-friendly")
        if calories < 400:
            health_insights.append("✅ Low calorie - good for weight management")
        
        return {
            "recipe_title": recipe.get('title', 'Recipe'),
            "servings": recipe.get('servings', 1),
            "ready_in_minutes": recipe.get('readyInMinutes', 'N/A'),
            "health_score": recipe.get('healthScore', 0),
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
            "fiber": fiber,
            "sodium": sodium,
            "health_insights": health_insights
        }
    except:
        return {"error": "Nutrition analysis failed"}

@tool
def estimate_costs(ingredients: List[str], servings: int = 4) -> Dict:
    """Detailed cost estimation with budget tips."""
    prices = {
        "chicken breast": 6.99, "ground beef": 5.99, "salmon": 12.99,
        "rice": 2.99, "pasta": 1.99, "broccoli": 2.99, "tomatoes": 3.99,
        "cheese": 5.99, "onion": 1.49, "garlic": 2.99, "olive oil": 7.99
    }
    
    cost_breakdown = []
    total_cost = 0
    
    for ingredient in ingredients:
        ingredient_lower = ingredient.lower().strip()
        cost = 3.99  # default
        
        for key, price in prices.items():
            if key in ingredient_lower or any(word in ingredient_lower for word in key.split()):
                cost = price
                break
        
        adjusted_cost = (cost * servings) / 4
        total_cost += adjusted_cost
        cost_breakdown.append({
            "name": ingredient.title(),
            "cost": round(adjusted_cost, 2)
        })
    
    # Budget tips
    budget_tips = []
    if total_cost > 30:
        budget_tips.append("💡 Consider buying in bulk for better prices")
    if total_cost > 40:
        budget_tips.append("💡 Look for seasonal alternatives to reduce costs")
    budget_tips.append("💡 Shop at local markets for fresher, cheaper produce")
    
    return {
        "total_cost": round(total_cost, 2),
        "cost_per_serving": round(total_cost / servings, 2),
        "servings": servings,
        "breakdown": cost_breakdown,
        "budget_tips": budget_tips
    }

@tool
def create_meal_plan(dietary_preference: str = "balanced", people: int = 2, days: int = 7, budget: str = "moderate") -> Dict:
    """Create comprehensive weekly meal plan with nutrition and shopping list."""
    
    meals = {
        "breakfast": [
            {"name": "Overnight Oats with Berries", "calories": 320, "protein": 12, "cost": 2.50},
            {"name": "Veggie Scramble with Toast", "calories": 280, "protein": 18, "cost": 3.20},
            {"name": "Greek Yogurt Parfait", "calories": 250, "protein": 15, "cost": 2.80}
        ],
        "lunch": [
            {"name": "Quinoa Buddha Bowl", "calories": 420, "protein": 16, "cost": 4.50},
            {"name": "Chicken Caesar Wrap", "calories": 380, "protein": 25, "cost": 5.20},
            {"name": "Lentil Vegetable Soup", "calories": 340, "protein": 18, "cost": 3.80}
        ],
        "dinner": [
            {"name": "Grilled Salmon with Vegetables", "calories": 520, "protein": 35, "cost": 8.90},
            {"name": "Chicken Stir Fry with Brown Rice", "calories": 480, "protein": 32, "cost": 6.50},
            {"name": "Vegetable Curry with Quinoa", "calories": 450, "protein": 15, "cost": 5.20}
        ]
    }
    
    budget_multipliers = {"low": 0.7, "moderate": 1.0, "high": 1.3}
    multiplier = budget_multipliers.get(budget.lower(), 1.0)
    
    weekly_plan = {}
    shopping_list = set()
    total_weekly_cost = 0
    total_weekly_calories = 0
    total_weekly_protein = 0
    
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for day in day_names[:days]:
        daily_meals = {}
        daily_calories = 0
        daily_protein = 0
        daily_cost = 0
        
        for meal_type in ["breakfast", "lunch", "dinner"]:
            selected_meal = random.choice(meals[meal_type])
            daily_meals[meal_type] = {
                "name": selected_meal["name"],
                "calories": selected_meal["calories"],
                "protein": selected_meal["protein"]
            }
            
            meal_cost = selected_meal["cost"] * people * multiplier
            daily_calories += selected_meal["calories"]
            daily_protein += selected_meal["protein"]
            daily_cost += meal_cost
            
            # Add to shopping list
            if "chicken" in selected_meal["name"].lower():
                shopping_list.add("Chicken breast")
            if "salmon" in selected_meal["name"].lower():
                shopping_list.add("Salmon fillets")
            if "vegetable" in selected_meal["name"].lower():
                shopping_list.update(["Mixed vegetables", "Onions", "Garlic"])
            if "quinoa" in selected_meal["name"].lower():
                shopping_list.add("Quinoa")
            if "oats" in selected_meal["name"].lower():
                shopping_list.add("Rolled oats")
        
        weekly_plan[day] = daily_meals
        total_weekly_cost += daily_cost
        total_weekly_calories += daily_calories
        total_weekly_protein += daily_protein
    
    # Generate insights
    avg_daily_calories = round(total_weekly_calories / days)
    avg_daily_protein = round(total_weekly_protein / days, 1)
    
    insights = []
    if avg_daily_calories < 1800:
        insights.append("⚠️ Consider adding healthy snacks to meet calorie needs")
    elif avg_daily_calories > 2200:
        insights.append("💡 Calorie-dense meals - great for active lifestyles")
    
    if avg_daily_protein > 80:
        insights.append("✅ Excellent protein intake for muscle maintenance")
    elif avg_daily_protein < 60:
        insights.append("💡 Consider adding more protein sources")
    
    return {
        "meal_plan": weekly_plan,
        "total_weekly_cost": round(total_weekly_cost, 2),
        "cost_per_person_per_day": round(total_weekly_cost / (people * days), 2),
        "avg_daily_calories": avg_daily_calories,
        "avg_daily_protein": avg_daily_protein,
        "dietary_preference": dietary_preference,
        "serves": people,
        "days": days,
        "shopping_list": sorted(list(shopping_list)),
        "insights": insights
    }

async def create_agent():
    agent = Agent(
        name="MealPlanningExpert",
        model=OpenAIChat(id="gpt-5-mini"),
        tools=[search_recipes, analyze_nutrition, estimate_costs, create_meal_plan, DuckDuckGoTools()],
        instructions=dedent("""\
            You are an expert meal planning assistant. Provide detailed, helpful responses:
            
            🔍 **Recipe Searches**: Include cooking time, health scores, ingredient lists, and instructions
            📊 **Nutrition Analysis**: Provide health insights, nutritional breakdowns, and dietary advice
            💰 **Cost Estimation**: Include budget tips and cost per serving breakdowns
            📅 **Meal Planning**: Create detailed weekly plans with nutritional balance and shopping lists
            
            **Always**:
            - Use clear headings and bullet points
            - Include practical cooking tips
            - Consider dietary restrictions and budgets
            - Provide actionable next steps
            - Be encouraging and supportive
        """),
        markdown=True,
        debug_mode=True
    )
    return agent

def main():
    st.set_page_config(page_title="AI Meal Planning Agent", page_icon="🍽️", layout="wide")
    
    st.title("🍽️ AI Meal Planning Agent")
    st.markdown("*Your intelligent companion for recipes, nutrition, and meal planning*")
    
    if not OPENAI_API_KEY:
        st.error("Please add OPENAI_API_KEY to your .env file")
        st.stop()
    
    # Initialize agent
    if "agent" not in st.session_state:
        with st.spinner("Initializing agent..."):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                st.session_state.agent = loop.run_until_complete(create_agent())
            except Exception as e:
                st.error(f"Failed to initialize agent: {e}")
                st.stop()
    
    # Initialize messages
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": """👋 **Welcome! I'm your AI Meal Planning Expert.**

I can help you with:
- 🔍 **Recipe Discovery** - Find recipes based on your ingredients
- 📊 **Nutrition Analysis** - Get detailed nutritional insights
- 💰 **Cost Estimation** - Smart budget planning with money-saving tips
- 📅 **Meal Planning** - Complete weekly meal plans with shopping lists

**Try asking:**
- "Find healthy chicken recipes for dinner"
- "What's the nutrition info for chicken teriyaki?"
- "Create a vegetarian meal plan for 2 people for one week"
- "Estimate costs for pasta, tomatoes, cheese, and basil for 4 servings"

What would you like to explore? 🍽️"""
        }]
    
    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if user_input := st.chat_input("Ask about recipes, nutrition, meal planning, or costs..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response: RunOutput = loop.run_until_complete(
                        st.session_state.agent.arun(user_input)
                    )
                    
                    st.markdown(response.content)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response.content
                    })
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

if __name__ == "__main__":
    main()