import streamlit as st
from phi.agent import Agent
from phi.model.anthropic import Claude
from phi.model.google import Gemini

def display_dietary_plan(plan_content):
    st.subheader("Dietary Plan")
    st.markdown(
        f"""
        ### Why this plan works:
        {plan_content["why_this_plan_works"]}
        
        ### Meal Plan:
        {plan_content["meal_plan"]}
        
        ### Important Considerations:
        {plan_content["important_considerations"]}
        """
    )

# Function to format and display the fitness plan
def display_fitness_plan(plan_content):
    st.subheader("Fitness Plan")
    st.markdown(
        f"""
        ### Goals:
        {plan_content["goals"]}
        
        ### Exercise Routine:
        {plan_content["routine"]}
        
        ### Tips:
        {plan_content["tips"]}
        """
    )

# Set up the Streamlit app
st.title("AI Health and Fitness Agent 🏋️‍♂️")
st.caption("Get personalized dietary and fitness plans based on your preferences and goals.")

# Use st.secrets for API key in production
gemini_api_key = st.sidebar.text_input("Enter Gemini API Key for health and fitness data", type="password")

if gemini_api_key:
    st.success("Gemini API Key accepted! Please fill out your profile below.")
    
    # Initialize the Gemini model once
    try:
        gemini_model = Gemini(id="gemini-1.5-flash", api_key=gemini_api_key)
    except Exception as e:
        st.error(f"Error initializing Gemini model: {e}")
        st.stop()

    # Input fields for user's profile
    st.header("User Profile")
    age = st.number_input("Age", min_value=10, max_value=100, step=1)
    weight = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, step=0.1)
    height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, step=0.1)
    sex = st.selectbox("Sex", options=["Male", "Female", "Other"])
    activity_level = st.selectbox(
        "Activity Level",
        options=["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"],
    )
    dietary_preferences = st.selectbox("Diet Preferences",
                                       options=["Vegetarian", "keto", "Gluten free", "Low Carb", "Dairy free"])
    fitness_goals = st.selectbox(
        "Fitness Goals",
        options=["Lose Weight", "Gain Muscle", "Endurance", "Stay Fitness", "strength training"],
    )
    if st.button("Generate Personalized Plan"):
        with st.spinner("Giving you the best Health and Fitness Routine! Patience my guy ;)"):
            try:
                # Define the Dietary Agent
                dietary_agent = Agent(
                    name="Dietary Agent",
                    role="Provides personalized dietary recommendations",
                    model=gemini_model,
                    instructions=[
                        "Consider the user's input, including dietary restrictions and preferences.",
                        "Suggest a detailed meal plan for the day, including breakfast, lunch, dinner, and snacks.",
                        "Provide a brief explanation of why the plan is suited to the user's goals.",
                        "Focus on clarity, coherence, and quality of the recommendations.",
                    ],
                    add_history_to_messages=True,
                    markdown=True,
                )

                # Define the Fitness Agent
                fitness_agent = Agent(
                    name="Fitness Agent",
                    role="Provides personalized fitness recommendations",
                    model=gemini_model,
                    instructions=[
                        "Provide exercises tailored to the user's goals (e.g., weight loss, muscle gain, general fitness).",
                        "Include warm-up, main workout, and cool-down exercises.",
                        "Explain the benefits of each recommended exercise.",
                        "Ensure the plan is actionable, detailed, and motivational.",
                    ],
                    add_history_to_messages=True,
                    markdown=True,
                )

                # Compile user input into a profile
                user_profile = f"Age: {age}, Weight: {weight}kg, Height: {height}cm, Sex: {sex}, Activity Level: {activity_level}, Dietary Preferences: {dietary_preferences}, Fitness Goals: {fitness_goals}"

                dietary_plan_response = dietary_agent.run(user_profile)
                dietary_plan = {
                    "why_this_plan_works": "High Protein, Healthy Fats, Moderate Carbohydrates, and Caloric Surplus.",
                    "meal_plan": dietary_plan_response.content,
                    "important_considerations": """
                    - Hydration: Drink plenty of water.
                    - Electrolytes: Monitor sodium, potassium, and magnesium levels.
                    - Fiber: Ensure adequate intake through vegetables.
                    - Listen to your body: Adjust portion sizes as needed.
                    """,
                }
                display_dietary_plan(dietary_plan)

                # Generate Fitness Plan
                fitness_plan_response = fitness_agent.run(user_profile)
                fitness_plan = {
                    "goals": "Build muscle strength and endurance.",
                    "routine": fitness_plan_response.content,
                    "tips": """
                    - Track Progress: Record weights and reps to ensure progressive overload.
                    - Rest: Allow at least 48 hours between sessions for recovery.
                    - Consistency: Stick to the plan for optimal results.
                    """,
                }
                display_fitness_plan(fitness_plan)


            except Exception as e:
                st.error(f"An error occurred: {e}")
else:
     st.warning("Please enter your Gemini API Key to proceed. go get it here: https://aistudio.google.com/apikey")
