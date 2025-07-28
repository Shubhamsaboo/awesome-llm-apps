import streamlit as st
import pickle
import pandas as pd
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MODEL_PATH = Path('xgboost_cvd_predictor.pkl')
IMAGE_PATH = Path('thumbnail.jpg')

# Data mappings
MAPPINGS = {
    "race_options": {
        "American Indian/Alaskan Native": 0,
        "White": 5,
        "Black": 2,
        "Asian": 1,
        "Hispanic": 3,
        "Other": 4
    },
    "sex_options": {"Male": 1, "Female": 0},
    "age_categories": {
        "18-24": 0, "25-29": 1, "30-34": 2, "35-39": 3, "40-44": 4,
        "45-49": 5, "50-54": 6, "55-59": 7, "60-64": 8, "65-69": 9,
        "70-74": 10, "75-79": 11, "80 or older": 12
    },
    "bmi_categories": {
        "Underweight (BMI: below 18.5)": 3,
        "Normal weight (BMI: 18.5-25)": 0,
        "Overweight (BMI: 25-30)": 2,
        "Obese (BMI: above 30)": 1
    },
    "general_health_options": {
        "Excellent": 0, "Very Good": 4, "Good": 2, "Fair": 1, "Poor": 3
    },
    "binary_options": {"No": 0, "Yes": 1},
    "diabetes_categories": {
        "Yes (during pregnancy)": 3,
        "No, borderline diabetes": 1,
        "No": 0,
        "Yes": 2
    }
}

class CardiovascularDiseasePredictor:
    def __init__(self):
        self.model = self._load_model()
        self.setup_page()
        
    @staticmethod
    def _load_model():
        """Load the XGBoost model from pickle file."""
        try:
            with open(MODEL_PATH, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            st.error("Error loading the prediction model. Please contact support.")
            return None

    def setup_page(self):
        """Setup the Streamlit page layout and navigation."""
        st.set_page_config(
            page_title="Cardiovascular Diseases (CVD) Predictor",
            page_icon="❤️",
            layout="wide"
        )
        
        with st.sidebar:
            self.selected = st.selectbox(
                'Select Disease',
                ['Cardiovascular Disease (CVD) Prediction','Heart Disease Prediction (Under Development)', 'Diabetes Prediction (Under Development)'],
                index=0
            )

    def display_description(self):
        """Display the application description and author information."""
        st.image(str(IMAGE_PATH), caption="Provide the inputs on the left. I'll help you diagnose your cardiovascular health!", width=340)
        st.markdown("### About the Application")
        st.markdown("""
        This AI-powered application helps predict your Cardiovascular Disease (CVD) risk using advanced machine learning.
        
        **Key Features:**
        - 91.5% prediction accuracy
        - Trained on 300,000+ US health records
        - Real-time risk assessment
        - Easy-to-understand results
        
        **Important:** This tool is for educational purposes only and should not replace professional medical advice.
        
        **Author:** jvc-Byte  
        **Contact:** [Email](mailto:jvc8463@gmail.com)
        """)

    def get_user_inputs(self):
        """Collect and validate user inputs."""
        with st.form("health_info_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                inputs = {
                    'Race': st.selectbox("Race:", list(MAPPINGS['race_options'].keys())),
                    'Sex': st.selectbox("Sex:", list(MAPPINGS['sex_options'].keys())),
                    'AgeCategory': st.selectbox("Age Category:", list(MAPPINGS['age_categories'].keys())),
                    'BMICategory': st.selectbox("BMI Category:", list(MAPPINGS['bmi_categories'].keys())),
                    'GenHealth': st.selectbox("General Health:", list(MAPPINGS['general_health_options'].keys())),
                    'SleepTime': st.number_input("Average Sleep Hours:", 0, 24, 7),
                    'PhysicalActivity': st.selectbox("Sports Activity in Past Month:", ["No", "Yes"]),
                    'Smoking': st.selectbox("Smoked 100+ Cigarettes Lifetime:", ["No", "Yes"]),
                }
            
            with col2:
                inputs.update({
                    'AlcoholDrinking': st.selectbox("Heavy Alcohol Consumption:", ["No", "Yes"]),
                    'PhysicalHealth': st.slider("Days of Poor Physical Health (Past 30 Days):", 0, 30, 0),
                    'MentalHealth': st.slider("Days of Poor Mental Health (Past 30 Days):", 0, 30, 0),
                    'DiffWalking': st.selectbox("Difficulty Walking:", ["No", "Yes"]),
                    'Diabetic': st.selectbox("Diabetes Status:", list(MAPPINGS['diabetes_categories'].keys())),
                    'Stroke': st.selectbox("Previous Stroke:", ["No", "Yes"]),
                    'Asthma': st.selectbox("Asthma:", ["No", "Yes"]),
                    'KidneyDisease': st.selectbox("Kidney Disease:", ["No", "Yes"]),
                    'SkinCancer': st.selectbox("Skin Cancer:", ["No", "Yes"])
                })
            
            submitted = st.form_submit_button("Predict CVD Risk")
            return inputs, submitted

    def prepare_input_data(self, inputs):
        """Transform user inputs into model-ready format."""
        transformed_inputs = {
            'BMICategory': MAPPINGS['bmi_categories'][inputs['BMICategory']],
            'Smoking': MAPPINGS['binary_options'][inputs['Smoking']],
            'AlcoholDrinking': MAPPINGS['binary_options'][inputs['AlcoholDrinking']],
            'Stroke': MAPPINGS['binary_options'][inputs['Stroke']],
            'PhysicalHealth': inputs['PhysicalHealth'],
            'MentalHealth': inputs['MentalHealth'],
            'DiffWalking': MAPPINGS['binary_options'][inputs['DiffWalking']],
            'Sex': MAPPINGS['sex_options'][inputs['Sex']],
            'AgeCategory': MAPPINGS['age_categories'][inputs['AgeCategory']],
            'Race': MAPPINGS['race_options'][inputs['Race']],
            'Diabetic': MAPPINGS['diabetes_categories'][inputs['Diabetic']],
            'PhysicalActivity': MAPPINGS['binary_options'][inputs['PhysicalActivity']],
            'GenHealth': MAPPINGS['general_health_options'][inputs['GenHealth']],
            'SleepTime': inputs['SleepTime'],
            'Asthma': MAPPINGS['binary_options'][inputs['Asthma']],
            'KidneyDisease': MAPPINGS['binary_options'][inputs['KidneyDisease']],
            'SkinCancer': MAPPINGS['binary_options'][inputs['SkinCancer']]
        }
        return pd.DataFrame([transformed_inputs])

    def predict_and_display(self, input_data):
        """Make prediction and display results."""
        try:
            prediction_proba = self.model.predict_proba(input_data)[:, 1]
            probability = round(prediction_proba[0] * 100, 2)
            
            risk_zones = {
                (0, 25): ("green zone", "#32CD32", "Low risk. Continue maintaining a healthy lifestyle."),
                (25, 50): ("yellow zone", "#FFD700", "Moderate risk. Consider lifestyle improvements."),
                (50, 75): ("orange zone", "#FF4500", "High risk. Consultation with a doctor is recommended."),
                (75, 101): ("red zone", "#DC143C", "Very high risk. Please seek medical advice promptly.")
            }
            
            for (lower, upper), (zone, color, message) in risk_zones.items():
                if lower <= probability < upper:
                    st.markdown(
                        f"""
                        <div style='padding: 20px; border-radius: 10px; background-color: {color}20;'>
                            <h2 style='color: {color}'>Cardiovascular Disease (CVD) Risk: {probability}%</h2>
                            <p style='color: {color}'>You are in the {zone}. {message}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    break
            
            # Display health recommendations
            self.display_recommendations(probability)
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            st.error("An error occurred during prediction. Please try again.")

    def display_recommendations(self, risk_probability):
        """Display health recommendations based on risk level."""
        st.markdown("### Health Recommendations")
        
        recommendations = [
            "🏃‍♂️ Maintain regular physical activity (150 minutes/week)",
            "🥗 Follow a Cardiovascular-healthy diet",
            "😴 Get 5-8 hours of quality sleep",
            "🚭 Quit smoking if applicable",
            "🍷 Limit alcohol consumption",
            "⚕️ Regular health check-ups"
        ]
        
        for rec in recommendations:
            st.markdown(f"- {rec}")
        
        if risk_probability > 50:
            st.warning("⚠️ Given your risk level, we strongly recommend consulting a healthcare provider.")

    def run(self):
        """Main application loop."""
        if self.selected == 'Cardiovascular Disease (CVD) Prediction':
            st.title('🏥 Cardiovascular Disease Risk Predictor 🏥')
            
            col1, col2 = st.columns([3, 2])
            
            with col1:
                inputs, submitted = self.get_user_inputs()
            
            with col2:
                self.display_description()
            
            if submitted:
                input_data = self.prepare_input_data(inputs)
                self.predict_and_display(input_data)
        elif self.selected == 'Heart Disease Prediction (Under Development)':
            st.info("Heart Disease Prediction feature is under development. Please check back later!")
        else:
            st.info("Diabetes Prediction feature is under development. Please check back later!")

if __name__ == "__main__":
    app = CardiovascularDiseasePredictor()
    app.run()