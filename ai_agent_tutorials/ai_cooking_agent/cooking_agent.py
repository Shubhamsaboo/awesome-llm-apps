from pydantic import BaseModel, Field
from typing import List
from phi.agent import Agent
import streamlit as st
from phi.model.google import Gemini
import json

class MealPlan(BaseModel):
    meal_name: str = Field(..., description="Name of the meal, e.g., Breakfast, Lunch, or Dinner")
    recipe: str = Field(..., description="Short description of the recipe")
    ingredients: List[str] = Field(..., description="List of ingredients needed for this meal")
    instructions: str = Field(..., description="Brief cooking instructions")
    grocery_list: List[str] = Field(..., description="List of groceries required for the meal")

# Set up the Streamlit app
st.title("AI Cooking Assistant 🍲")
st.caption("Discover recipes, plan meals, and cook like a chef with a personalized AI Cooking Assistant powered by GEMINI")

# Get GEMINI API key from user
gemini_api_key = st.text_input("Enter GEMINI API Key", type="password")

if gemini_api_key:
    recipe_researcher = Agent(
        model=Gemini(id="gemini-1.5-flash", api_key=gemini_api_key),
        description=
            """
            You are a master culinary researcher. Based on the ingredients, cuisine type, or specific dietary needs,
            generate a list of search terms for finding relevant recipes and cooking methods. Then search the web using each term,
            analyze the results, and return the most useful recipe options and cooking tips for the user.
            """,
        instructions=[
            "Given user input on ingredients, cuisine type, or dietary preferences, generate 3 search terms for each category.",
            "Use `search_google` for each term and analyze the results.",
            "Select the 10 most relevant and varied recipes and cooking methods.",
            "Focus on diverse cuisine options and interesting recipe variations.",
        ],
        add_datetime_to_instructions=True,
    )
    
    meal_planner = Agent(
    model=Gemini(id="gemini-1.5-flash", api_key=gemini_api_key),
    description="You are a skilled meal planner who generates structured meal plans with recipes, ingredients, and instructions.",
    response_model=MealPlan,
    instructions=[
        "Generate a structured meal plan with the following details: meal name, recipe description, ingredients list, cooking instructions, and grocery list.",
        "Use a consistent structure for each meal in the plan, including clearly labeled sections for each part.",
        "Provide grocery lists, preparation steps, and useful cooking tips for each meal.",
    ],
    add_datetime_to_instructions=True,
    add_chat_history_to_prompt=True,
    num_history_messages=3,
)

    # Input fields for user preferences
    ingredients = st.text_area("What ingredients do you have or want to use?")
    cuisine_type = st.text_input("Any specific cuisine or dietary preference?")
    num_meals = st.number_input("How many meals would you like to plan for?", min_value=1, max_value=5, value=2)

    if st.button("Generate Meal Plan"):
        with st.spinner("Whipping up the perfect recipes..."):
        # Get the structured response from the meal planner
            response = meal_planner.run(
                f"{cuisine_type} recipes using {ingredients} for {num_meals} meals",
                stream=False,
            )
            recipes  = response.content
            corrected_data = f'[{recipes}]'
            parsed_data = json.loads(corrected_data)
            st.write(response)

            for item in parsed_data:
                st.subheader(f"🍲 Dish Name: {item['meal_name']}")
                st.markdown(f"**Recipe**: {item['recipe']}")

                # Display Ingredients as bullet points
                st.markdown("### Ingredients")
                for ingredient in item['ingredients']:
                    st.markdown(f"- {ingredient}")

                # Display Instructions as numbered steps
                st.markdown("### Instructions")
                st.markdown(item['instructions'])

                # Display Grocery List as bullet points
                st.markdown("### Grocery List")
                for grocery_item in item['grocery_list']:
                    st.markdown(f"- {grocery_item}")

                st.markdown("---")  # Divider between recipes