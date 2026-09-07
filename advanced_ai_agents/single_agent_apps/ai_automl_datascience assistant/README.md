# AI-Driven ML and Data Science Assistant

An intelligent, AI-powered assistant for automated machine learning and data science tasks built with LangGraph and LLM integration.

## Overview

This Jupyter notebook provides an interactive assistant that leverages LLMs (via Groq/OpenAI) to automate common data science workflows. It's designed to work with datasets like the NY House Dataset and can perform comprehensive data analysis, preprocessing, and model training with natural language queries.

## Key Features

- **Data Exploration**: Automatically inspect dataset structure, columns, and statistics
- **Data Cleaning**: Detect and handle missing values, outliers, and anomalies
- **Data Type Detection**: Auto-detect and validate column data types
- **Statistical Analysis**: Generate column distributions and statistical summaries
- **Model Training**: Train and evaluate multiple classification and regression models
- **Cross-Validation**: Built-in cross-validation support for robust model evaluation
- **Natural Language Interface**: Chat-based interaction with the AI assistant
- **Visualization**: Integrate seaborn and matplotlib for data insights

## Requirements

The notebook installs the following dependencies:

```
pandas, numpy, langchain, scikit-learn, optuna, openai, langchain_openai, 
kagglehub, langgraph, langgraph-sdk, langgraph-checkpoint-sqlite, langsmith, 
matplotlib, seaborn, langchain_nvidia_ai_endpoints, umap-learn, langchain_groq
```

## Setup

1. **Install Dependencies**: Run the setup cells to install all required libraries
2. **Configure Environment**: Set up API keys for Groq/OpenAI (handled via environment variables)
3. **Load Dataset**: The notebook imports the NY House Dataset from Kaggle
4. **Initialize LLM**: Connects to Groq's LLM with GPT-OSS-120B model

## Main Components

### Tools & Utilities
- `check_missing_values()` - Identifies missing data
- `get_dataset_info()` - Returns dataset shape, columns, and types
- `get_column_stats()` - Computes statistical summaries
- `detect_and_handle_outliers()` - Identifies and manages anomalies
- `analyze_column_distribution()` - Creates distribution visualizations
- `auto_detect_data_types()` - Infers and validates data types
- `train_and_evaluate_classification_models()` - Trains classification models with CV
- `train_and_evaluate_regression_models()` - Trains regression models with CV
- `operations_on_dataset()` - Performs data transformations
- `save_dataframe_to_csv()` - Exports processed data

### LangGraph Integration
The notebook uses LangGraph to create an agentic workflow where the LLM:
- Selects appropriate tools based on user queries
- Orchestrates multi-step data analysis pipelines
- Maintains conversation context across interactions

## Usage

1. Run all setup cells to initialize the assistant
2. Use the chat interface to query the dataset:
   ```
   Example: "What's the overall structure of the dataset?"
   Example: "Can you analyze the 'price' column?"
   ```
3. Type `exit` to end the conversation

## Model Support

- **Classification**: Logistic Regression, Random Forest, SVM, Decision Tree
- **Regression**: Linear Regression, Random Forest Regressor, SVR, Decision Tree Regressor
- **Preprocessing**: StandardScaler, MinMaxScaler, PolynomialFeatures, LabelEncoder

## Author

**N. Kushwanth**

## License

This notebook is provided as-is for educational and research purposes.
