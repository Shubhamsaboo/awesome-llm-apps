"""
Module for preprocessing data before model training.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

def identify_column_types(df):
    """
    Automatically identify numerical and categorical columns
    
    Args:
        df: Input DataFrame
        
    Returns:
        tuple: (numerical_columns, categorical_columns)
    """
    numerical_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
    
    return numerical_columns, categorical_columns

def preprocess_data(data, target_column, features=None):
    """
    Preprocess data for model training
    
    Args:
        data: Input DataFrame
        target_column: Name of the target column
        features: List of feature columns (if None, all columns except target are used)
        
    Returns:
        tuple: (X_processed, y, preprocessor)
    """
    # Copy data to avoid modifying the original
    df = data.copy()
    
    # Handle missing target values
    if df[target_column].isna().any():
        df = df.dropna(subset=[target_column])
    
    # Select features
    if features is None:
        features = [col for col in df.columns if col != target_column]
    
    X = df[features]
    y = df[target_column]
    
    # Identify column types
    numerical_columns, categorical_columns = identify_column_types(X)
    
    # Create preprocessing pipeline
    numerical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, numerical_columns),
            ('cat', categorical_transformer, categorical_columns)
        ],
        remainder='drop'
    )
    
    # Apply preprocessing
    X_processed = preprocessor.fit_transform(X)
    
    # If X_processed is a numpy array, convert it to DataFrame with feature names
    if isinstance(X_processed, np.ndarray):
        # Get feature names from preprocessor
        feature_names = []
        
        # Add numerical column names
        if numerical_columns:
            feature_names.extend(numerical_columns)
        
        # Add transformed categorical column names
        if categorical_columns:
            for cat_col in categorical_columns:
                # Get categories for this column
                cat_idx = preprocessor.transformers_[1][2].index(cat_col)
                categories = preprocessor.transformers_[1][1].named_steps['onehot'].categories_[cat_idx]
                feature_names.extend([f"{cat_col}_{cat}" for cat in categories])
        
        X_processed = pd.DataFrame(X_processed, columns=feature_names, index=X.index)
    
    return X_processed, y, preprocessor