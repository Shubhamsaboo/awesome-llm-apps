"""
Module for making predictions with trained machine learning models.
"""
import joblib
import pandas as pd
import numpy as np
import os
import hashlib

def load_model(model_filename):
    """
    Load a saved model from disk
    
    Args:
        model_filename: Name of the model file
        
    Returns:
        The loaded model
    """
    try:
        return joblib.load(f"models/{model_filename}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Model file not found: {model_filename}")

def make_prediction(model_results, input_data):
    """
    Make predictions using a trained model
    
    Args:
        model_results: Results from training including model and preprocessor
        input_data: Input data for prediction (dict, list, or DataFrame)
        
    Returns:
        Prediction results
    """
    model = model_results.get('model')
    if model is None:
        model_filename = model_results.get('model_filename')
        if model_filename:
            model = load_model(model_filename)
        else:
            raise ValueError("No model provided for prediction")
    
    preprocessor = model_results.get('preprocessor')
    feature_names = model_results.get('feature_names', [])
    
    # Convert input data to DataFrame if it's not already
    if isinstance(input_data, dict):
        input_df = pd.DataFrame([input_data])
    elif isinstance(input_data, list) and all(isinstance(x, dict) for x in input_data):
        input_df = pd.DataFrame(input_data)
    elif not isinstance(input_data, pd.DataFrame):
        raise ValueError("Input data must be a dict, list of dicts, or DataFrame")
    
    # Ensure input data has the expected columns
    if feature_names:
        missing_cols = set(feature_names) - set(input_df.columns)
        if missing_cols:
            raise ValueError(f"Input data is missing required columns: {missing_cols}")
        
        # Select only relevant columns in the right order
        input_df = input_df[feature_names]
    
    # Apply preprocessing if available
    if preprocessor:
        input_data_processed = preprocessor.transform(input_df)
    else:
        input_data_processed = input_df
    
    # Make prediction
    prediction = model.predict(input_data_processed)
    
    # For classification models, also get probabilities if available
    if hasattr(model, 'predict_proba'):
        try:
            probabilities = model.predict_proba(input_data_processed)
            return {'prediction': prediction, 'probabilities': probabilities}
        except:
            pass
    
    return {'prediction': prediction}

def batch_predict(model_results, input_file):
    """
    Make batch predictions on a CSV file
    
    Args:
        model_results: Results from training including model and preprocessor
        input_file: Path to CSV file with input data
        
    Returns:
        DataFrame with predictions
    """
    # Load input data
    input_df = pd.read_csv(input_file)
    
    # Make predictions
    predictions = make_prediction(model_results, input_df)
    
    # Add predictions to input data
    result_df = input_df.copy()
    result_df['prediction'] = predictions['prediction']
    
    # Save results
    output_filename = f"predictions_{hashlib.md5(input_file.encode()).hexdigest()}.csv"
    os.makedirs('predictions', exist_ok=True)
    result_df.to_csv(f"predictions/{output_filename}", index=False)
    
    return {
        'predictions_df': result_df,
        'output_filename': output_filename
    }