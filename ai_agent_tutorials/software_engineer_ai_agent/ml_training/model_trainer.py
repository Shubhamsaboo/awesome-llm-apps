"""
Module for training machine learning models based on user requests.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report
import joblib
import os
import hashlib

from .preprocessing import preprocess_data

def train_model(data, model_type, target_column, features=None, test_size=0.2, random_state=42):
    """
    Train a machine learning model based on user specifications
    
    Args:
        data: DataFrame or path to CSV file
        model_type: Type of model to train ('regression', 'classification', etc.)
        target_column: Name of the target column
        features: List of feature columns (if None, all columns except target are used)
        test_size: Size of test split (default: 0.2)
        random_state: Random state for reproducibility
        
    Returns:
        dict: Results including trained model, metrics, and preprocessing objects
    """
    # Load and preprocess data
    if isinstance(data, str):
        # If data is a file path
        data = pd.read_csv(data)
    
    # Preprocess data
    X, y, preprocessor = preprocess_data(data, target_column, features)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    # Select and train model
    if model_type.lower() == 'linear_regression':
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = {
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': model.score(X_test, y_test)
        }
        model_class = 'regression'
    
    elif model_type.lower() == 'logistic_regression':
        model = LogisticRegression(random_state=random_state, max_iter=1000)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'classification_report': classification_report(y_test, y_pred)
        }
        model_class = 'classification'
    
    elif model_type.lower() == 'random_forest_classifier':
        model = RandomForestClassifier(random_state=random_state)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'classification_report': classification_report(y_test, y_pred)
        }
        model_class = 'classification'
    
    elif model_type.lower() == 'random_forest_regressor':
        model = RandomForestRegressor(random_state=random_state)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = {
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': model.score(X_test, y_test)
        }
        model_class = 'regression'
    
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    
    # Save model
    model_hash = hashlib.md5(f"{model_type}_{target_column}".encode()).hexdigest()
    model_filename = f"model_{model_hash}.joblib"
    
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, f"models/{model_filename}")
    
    return {
        'model': model,
        'model_filename': model_filename,
        'metrics': metrics,
        'preprocessor': preprocessor,
        'feature_names': X.columns.tolist(),
        'model_class': model_class,
        'model_type': model_type
    }

def evaluate_model(model_results, X_test, y_test):
    """
    Evaluate a trained model on test data
    
    Args:
        model_results: Results from training including model and metrics
        X_test: Test features
        y_test: Test targets
        
    Returns:
        dict: Updated metrics
    """
    model = model_results['model']
    model_class = model_results['model_class']
    
    if model_class == 'regression':
        y_pred = model.predict(X_test)
        metrics = {
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': model.score(X_test, y_test)
        }
    
    elif model_class == 'classification':
        y_pred = model.predict(X_test)
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'classification_report': classification_report(y_test, y_pred)
        }
    
    return metrics