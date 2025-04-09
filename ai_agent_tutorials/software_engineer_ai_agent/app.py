# Add these imports at the top of your app.py file
import os
import streamlit as st
import streamlit.components.v1 as components
import webbrowser
import traceback
import re
import tempfile
import hashlib
import time
import socket
import subprocess
import pandas as pd
import numpy as np
import pickle
import base64
import io
from dotenv import load_dotenv

from frontend.frontend_dev import generate_frontend_code
from backend.backend_dev import generate_backend_code
from dsa.dsa_solver import solve_dsa_problem
from utils.code_execution import execute_python_code
from utils.code_extractor import extract_code_block
from utils.code_validator import validate_code
from utils.secure_config import SecureConfig
from utils.port_utils import find_available_port
from utils.ml_training import train_model, clean_data, remove_low_variance_features, remove_correlated_features
from utils.ml_visualization import get_roc_curve, get_feature_importance, get_confusion_matrix, generate_classification_report

secure_config = SecureConfig()

def main():
    # Set page configuration
    st.set_page_config(
        page_title="AI Software Development Agent", 
        page_icon="💻", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for improved styling
    st.markdown("""
    <style>
    .main-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .code-output {
        background-color: #f4f4f4;
        border-radius: 5px;
        padding: 10px;
        max-height: 400px;
        overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'api_key_set' not in st.session_state:
        st.session_state.api_key_set = False

    # Main title with custom styling
    st.markdown("<h1 style='text-align: center; color: #2C3E50;'>🚀 AI Software Development Agent</h1>", unsafe_allow_html=True)

    # Sidebar for API Key and task selection
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("Enter your Gemini API Key", type="password")
        if api_key:
            # Securely store API key
            secure_config.store_api_key(st.session_state, api_key)
            st.session_state.api_key_set = True
            
            # Set the API key for current session
            retrieved_api_key = secure_config.get_api_key(st.session_state)
            if retrieved_api_key:
                os.environ["GOOGLE_API_KEY"] = retrieved_api_key

        task = st.selectbox("Select a task:", [
            "Frontend Development", 
            "Backend Development", 
            "DSA Problem Solving",
            "Machine Learning"
        ])

    # Main content area
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Task-specific sections with error handling
    try:
        if task == "Frontend Development":
            frontend_development()
        elif task == "Backend Development":
            backend_development()
        elif task == "DSA Problem Solving":
            dsa_problem_solving()
        elif task == "Machine Learning":
            ml_training_prediction()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        # Only log the full traceback, don't show it to users
        print(traceback.format_exc())

    st.markdown('</div>', unsafe_allow_html=True)

# Add this function to your app.py file
def ml_training_prediction():
    st.subheader("🤖 Machine Learning Model Training")
    
    # File uploader for CSV
    uploaded_file = st.file_uploader("Upload your CSV dataset", type=['csv'])
    
    if uploaded_file is not None:
        # Display dataset preview
        try:
            df = pd.read_csv(uploaded_file)
            st.write("### Dataset Preview:")
            st.dataframe(df.head())
            
            # Dataset info
            st.write("### Dataset Information:")
            buffer = io.StringIO()
            df.info(buf=buffer)
            info_str = buffer.getvalue()
            st.text(info_str)
            
            # Dataset statistics
            st.write("### Dataset Statistics:")
            st.dataframe(df.describe())
            
            # Missing values check
            missing_values = df.isnull().sum()
            if missing_values.sum() > 0:
                st.warning("⚠️ Your dataset contains missing values that will be handled during preprocessing.")
                st.dataframe(missing_values[missing_values > 0].rename("Missing Values Count"))
            
            # Select target column
            all_columns = df.columns.tolist()
            target_column = st.selectbox("Select target column for prediction:", all_columns)
            
            # Model training parameters
            st.subheader("Training Parameters")
            st.write("You can customize your model's parameters below:")
            
            model_type = st.selectbox(
                "Select model type:", 
                ["Random Forest", "Decision Tree", "Gradient Boosting"]
            )
            
            test_size = st.slider("Test set size (%):", 10, 50, 20)
            
            # Advanced parameters collapsible section
            with st.expander("Advanced Parameters"):
                if model_type == "Random Forest":
                    n_estimators = st.slider("Number of trees:", 50, 500, 100)
                    max_depth = st.slider("Maximum tree depth:", 3, 20, 10)
                    min_samples_split = st.slider("Minimum samples to split:", 2, 20, 2)
                    
                elif model_type == "Decision Tree":
                    max_depth = st.slider("Maximum tree depth:", 3, 20, 10)
                    min_samples_split = st.slider("Minimum samples to split:", 2, 20, 2)
                    criterion = st.selectbox("Criterion:", ["gini", "entropy"])
                    
                elif model_type == "Gradient Boosting":
                    n_estimators = st.slider("Number of trees:", 50, 500, 100)
                    learning_rate = st.slider("Learning rate:", 0.01, 0.3, 0.1, step=0.01)
                    max_depth = st.slider("Maximum tree depth:", 3, 10, 3)
            
            # Start training
            if st.button("Train Model"):
                with st.spinner("Training model... This may take a while..."):
                    try:
                        # Reset file pointer
                        uploaded_file.seek(0)
                        
                        # Prepare data
                        df = pd.read_csv(uploaded_file)
                        df = clean_data(df)
                        
                        # Split into features & labels
                        X = df.drop(columns=[target_column])
                        y = df[target_column]
                        
                        # Save original feature names
                        feature_names = X.columns.tolist()
                        
                        # Apply feature selection
                        X, variance_support = remove_low_variance_features(X.values)
                        X = remove_correlated_features(X)
                        
                        # Convert back to dataframe for better handling
                        X = pd.DataFrame(X)
                        
                        # Split dataset
                        from sklearn.model_selection import train_test_split
                        X_train, X_test, y_train, y_test = train_test_split(
                            X, y, test_size=test_size/100, random_state=42
                        )
                        
                        # Train model based on selection
                        if model_type == "Random Forest":
                            from sklearn.ensemble import RandomForestClassifier
                            model = RandomForestClassifier(
                                n_estimators=n_estimators,
                                max_depth=max_depth,
                                min_samples_split=min_samples_split,
                                random_state=42
                            )
                        elif model_type == "Decision Tree":
                            from sklearn.tree import DecisionTreeClassifier
                            model = DecisionTreeClassifier(
                                max_depth=max_depth,
                                min_samples_split=min_samples_split,
                                criterion=criterion,
                                random_state=42
                            )
                        elif model_type == "Gradient Boosting":
                            from sklearn.ensemble import GradientBoostingClassifier
                            model = GradientBoostingClassifier(
                                n_estimators=n_estimators,
                                learning_rate=learning_rate,
                                max_depth=max_depth,
                                random_state=42
                            )
                        
                        # Train the model
                        model.fit(X_train, y_train)
                        
                        # Model evaluation
                        st.success("✅ Model training completed!")
                        
                        # Show results in tabs
                        results_tab, viz_tab, download_tab = st.tabs(["Results", "Visualizations", "Download Model"])
                        
                        with results_tab:
                            # Model accuracy
                            train_score = model.score(X_train, y_train)
                            test_score = model.score(X_test, y_test)
                            
                            st.metric("Training Accuracy", f"{train_score:.2%}")
                            st.metric("Testing Accuracy", f"{test_score:.2%}")
                            
                            # Classification report
                            st.subheader("Classification Report")
                            report_html = generate_classification_report(model, X_test, y_test)
                            st.components.v1.html(report_html, height=300)
                        
                        with viz_tab:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # ROC curve
                                roc_fig = get_roc_curve(model, X_test, y_test)
                                if roc_fig:
                                    st.plotly_chart(roc_fig, use_container_width=True)
                                
                            with col2:
                                # Confusion matrix
                                cm_fig = get_confusion_matrix(model, X_test, y_test)
                                if cm_fig:
                                    st.plotly_chart(cm_fig, use_container_width=True)
                            
                            # Feature importance
                            st.subheader("Feature Importance")
                            feat_fig = get_feature_importance(model, feature_names[:X.shape[1]])
                            if feat_fig:
                                st.plotly_chart(feat_fig, use_container_width=True)
                            
                        with download_tab:
                            # Save the model to a file
                            model_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pkl")
                            with open(model_file.name, "wb") as f:
                                pickle.dump(model, f)
                            
                            # Generate model code for download
                            model_code = generate_model_code(model_type, model)
                            
                            # Provide download buttons
                            st.download_button(
                                label="Download Trained Model (.pkl)",
                                data=open(model_file.name, "rb").read(),
                                file_name=f"{model_type.lower().replace(' ', '_')}_model.pkl",
                                mime="application/octet-stream"
                            )
                            
                            st.download_button(
                                label="Download Model Code (.py)",
                                data=model_code,
                                file_name=f"{model_type.lower().replace(' ', '_')}_model.py",
                                mime="text/plain"
                            )
                            
                            # Clean up the temporary file
                            os.unlink(model_file.name)
                    
                    except Exception as e:
                        st.error(f"An error occurred during model training: {str(e)}")
                        # Log the full traceback but don't display it
                        print(traceback.format_exc())
        except Exception as e:
            st.error(f"Error processing the file: {str(e)}")
            st.write("Please ensure your CSV file is valid and try again.")

def generate_model_code(model_type, model):
    """Generate Python code for the trained model"""
    
    code = f"""# Generated {model_type} Model
import pandas as pd
import pickle
import numpy as np
from sklearn.preprocessing import LabelEncoder

# Load the trained model
def load_model(model_path='model.pkl'):
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

# Data preprocessing function
def preprocess_data(df):
    # Clean data
    df = df.drop_duplicates()  # Remove duplicates
    df = df.dropna()  # Remove missing values

    # Convert categorical columns to numeric using Label Encoding
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = LabelEncoder().fit_transform(df[col])

    return df

# Prediction function
def predict(input_data, model_path='model.pkl'):
    \"\"\"
    Make predictions using the trained model
    
    Args:
        input_data: DataFrame containing features
        model_path: Path to the saved model file
        
    Returns:
        Predictions
    \"\"\"
    # Load the model
    model = load_model(model_path)
    
    # Preprocess input data
    input_data = preprocess_data(input_data)
    
    # Make predictions
    predictions = model.predict(input_data)
    
    # Get prediction probabilities if available
    if hasattr(model, 'predict_proba'):
        probabilities = model.predict_proba(input_data)
        return predictions, probabilities
    
    return predictions, None

# Example usage
if __name__ == "__main__":
    # Example: Load test data
    # test_data = pd.read_csv('test_data.csv')
    
    # Example: Make predictions
    # predictions, probabilities = predict(test_data)
    
    # Example: Print results
    # print("Predictions:", predictions)
    # if probabilities is not None:
    #     print("Prediction probabilities:", probabilities)
    
    print("Model loaded successfully and ready to make predictions.")
"""
    
    return code

def sanitize_html(html_content):
    """
    Sanitize HTML content to prevent XSS attacks
    """
    # Basic sanitization - in production use a proper HTML sanitizer library
    # This is a simplified example
    html_content = re.sub(r'<script.*?>.*?</script>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'javascript:', '', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'on\w+\s*=', '', html_content, flags=re.IGNORECASE)
    return html_content

def write_file_securely(content, filename, file_type="txt"):
    """
    Write content to a file securely, with proper validation
    """
    # For Python code, validate before writing
    if file_type == "python":
        is_valid, issues = validate_code(content)
        if not is_valid:
            return False, issues
    
    # Use temporary file for secure writing
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp_name = temp.name
            temp.write(content.encode('utf-8'))
        
        # Move to final location
        os.replace(temp_name, filename)
        return True, None
    except Exception as e:
        return False, [str(e)]

def frontend_development():
    st.subheader("🌐 Frontend Website Generation")
    
    # Input and validation
    website_name = st.text_input("Enter website type (e.g., Portfolio, E-Commerce, Blog)")
    
    if st.button("Generate & Preview Website"):
        if not website_name:
            st.warning("Please enter a website type.")
            return

        with st.spinner("Generating frontend code..."):
            try:
                # Generate the full HTML response
                html_response = generate_frontend_code(website_name)
                
                # Extract only the HTML code
                html_code = extract_code_block(html_response, 'html')
                
                # Sanitize the HTML before displaying
                sanitized_html = sanitize_html(html_code)
                
                # Hash as filename for security
                filename = f"generated_site_{hashlib.md5(website_name.encode()).hexdigest()}.html"
                
                # Securely write to file
                success, issues = write_file_securely(sanitized_html, filename, "html")
                if not success:
                    st.error(f"Failed to save HTML file: {issues}")
                    return
                
                # Display preview using components.html with height limit
                st.subheader("Live Preview:")
                components.html(sanitized_html, height=600, scrolling=True)

                # Browser opening with error handling
                if st.button("Open in Browser"):
                    try:
                        webbrowser.open("file://" + os.path.abspath(filename))
                    except Exception as e:
                        st.error(f"Could not open browser: {str(e)}")

            except Exception as e:
                st.error(f"Error generating frontend code: {str(e)}")
                # Log the full traceback but don't display it
                print(traceback.format_exc())

def backend_development():
    st.subheader("🔧 Backend API Generation")
    
    api_description = st.text_area("Describe your API requirements")
    
    if st.button("Generate & Run API"):
        if not api_description:
            st.warning("Please provide API requirements.")
            return

        with st.spinner("Generating and launching backend code..."):
            try:
                # Generate the full backend code response
                backend_response = generate_backend_code(api_description)
                
                # Extract only the Python code
                backend_code = extract_code_block(backend_response, 'python')
                
                # Validate the code before displaying
                is_valid, issues = validate_code(backend_code)
                
                # Display code
                st.code(backend_code, language="python")
                
                if not is_valid:
                    st.error("Security issues detected in generated code:")
                    for issue in issues:
                        st.error(f"- {issue}")
                    return
                
                # Hash as filename for security
                filename = f"generated_api_{hashlib.md5(api_description.encode()).hexdigest()}.py"
                
                # Securely write to file
                success, issues = write_file_securely(backend_code, filename, "python")
                if not success:
                    st.error(f"Failed to save Python file: {issues}")
                    return
                
                # Execute the API in a separate process with a port checker
                available_port = find_available_port(8000, 9000)
                if available_port:
                    # Modify the code to use the available port if needed
                    if 'uvicorn.run' in backend_code:
                        # Attempt to modify the port in the code
                        modified_code = re.sub(
                            r'uvicorn\.run\(app,\s*host=["\']0\.0\.0\.0["\'],\s*port=\d+',
                            f'uvicorn.run(app, host="0.0.0.0", port={available_port}',
                            backend_code
                        )
                        # Write the modified code back to the file
                        success, issues = write_file_securely(modified_code, filename, "python")
                        if not success:
                            st.error(f"Failed to update port in API file: {issues}")
                            return
                
                    # Launch the API in a separate process
                    api_process = subprocess.Popen(
                        ["python", filename],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Wait a short time for the API to start
                    time.sleep(3)
                    
                    # Check if the process is still running
                    if api_process.poll() is None:
                        # Process is still running, API likely started successfully
                        st.success(f"🚀 API is running! You can test it at:")
                        api_url = f"http://localhost:{available_port}"
                        st.markdown(f"**API Base URL:** [{api_url}]({api_url})")
                        
                        # If FastAPI is detected, add a link to the docs
                        if "fastapi" in backend_code.lower():
                            docs_url = f"{api_url}/docs"
                            st.markdown(f"**Swagger UI:** [{docs_url}]({docs_url})")
                            
                            # Embed the Swagger UI in an iframe
                            st.subheader("API Documentation:")
                            components.iframe(docs_url, height=600, scrolling=True)
                    else:
                        # Process terminated, get the error
                        stdout, stderr = api_process.communicate()
                        st.error("API failed to start:")
                        st.code(stderr or stdout)
                else:
                    st.error("Could not find an available port to run the API.")

            except Exception as e:
                st.error(f"Error generating or running backend code: {str(e)}")
                # Log the full traceback but don't display it
                print(traceback.format_exc())

def dsa_problem_solving():
    st.subheader("📊 DSA Problem Solver")
    
    problem_statement = st.text_area("Describe your DSA problem")
    
    if st.button("Solve DSA Problem"):
        if not problem_statement:
            st.warning("Please provide a problem statement.")
            return

        with st.spinner("Solving DSA problem..."):
            try:
                # Generate the full DSA solution response
                dsa_response = solve_dsa_problem(problem_statement)
                
                # Extract only the Python code
                dsa_solution = extract_code_block(dsa_response, 'python')
                
                # Validate the code
                is_valid, issues = validate_code(dsa_solution)
                
                # Display code
                st.code(dsa_solution, language="python")
                
                if not is_valid:
                    st.error("Security issues detected in generated code:")
                    for issue in issues:
                        st.error(f"- {issue}")
                    return
                
                # Execute solution with error handling and timeout
                result = execute_python_code(dsa_solution, timeout=5)
                st.subheader("Output:")
                st.code(result)

            except Exception as e:
                st.error(f"Error solving DSA problem: {str(e)}")
                # Log the full traceback but don't display it
                print(traceback.format_exc())



if __name__ == "__main__":
    main()