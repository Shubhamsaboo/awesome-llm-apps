import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_selection import VarianceThreshold
import numpy as np
import tempfile

def clean_data(df):
    """Cleans the dataset by handling missing values and encoding categorical features."""
    df = df.drop_duplicates()  # Remove duplicates
    df = df.dropna()  # Remove missing values

    # Convert categorical columns to numeric using Label Encoding
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = LabelEncoder().fit_transform(df[col])

    return df

def remove_low_variance_features(X, threshold=0.01):
    """Removes features with low variance below the given threshold."""
    selector = VarianceThreshold(threshold)
    X_selected = selector.fit_transform(X)
    return X_selected, selector.get_support()

def remove_correlated_features(X, threshold=0.9):
    """Removes highly correlated features to avoid redundancy."""
    corr_matrix = pd.DataFrame(X).corr().abs()
    upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    # Identify columns to drop
    to_drop = [col for col in upper_triangle.columns if any(upper_triangle[col] > threshold)]
    X = pd.DataFrame(X).drop(columns=to_drop, axis=1)

    return X

def train_model(csv_file):
    """
    Reads CSV, cleans data, applies feature selection, trains a model, and returns the model file path.
    """
    try:
        df = pd.read_csv(csv_file)
        df = clean_data(df)

        # Split into features & labels (assumes last column is the target variable)
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]

        # Feature Selection Steps
        X, variance_support = remove_low_variance_features(X)
        X = remove_correlated_features(X)

        # Split dataset
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train a simple model (Random Forest)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Save the trained model to a file
        model_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pkl")
        with open(model_file.name, "wb") as f:
            pickle.dump(model, f)

        return model_file.name  # Return the path to the model file
    except Exception as e:
        return f"[ERROR] Failed to train model: {e}"
