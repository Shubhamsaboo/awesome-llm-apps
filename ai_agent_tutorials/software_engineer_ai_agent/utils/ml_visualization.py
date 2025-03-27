import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import io
import base64
from sklearn.metrics import roc_curve, auc, confusion_matrix, classification_report
import plotly.express as px
import plotly.graph_objects as go

def get_roc_curve(model, X_test, y_test):
    """Generate ROC curve and return the figure"""
    try:
        # Get probability predictions
        y_probs = model.predict_proba(X_test)
        
        # For multi-class, we'll use one-vs-rest approach
        if y_probs.shape[1] > 2:
            fig = go.Figure()
            for i in range(y_probs.shape[1]):
                y_true_binary = (y_test == i).astype(int)
                fpr, tpr, _ = roc_curve(y_true_binary, y_probs[:, i])
                auc_score = auc(fpr, tpr)
                fig.add_trace(go.Scatter(x=fpr, y=tpr,
                               mode='lines',
                               name=f'Class {i} (AUC = {auc_score:.3f})'))
            
            fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1],
                           mode='lines',
                           name='Random',
                           line=dict(dash='dash', color='gray')))
            
        else:  # Binary classification
            y_prob = y_probs[:, 1]
            fpr, tpr, _ = roc_curve(y_test, y_prob)
            auc_score = auc(fpr, tpr)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=fpr, y=tpr,
                           mode='lines',
                           name=f'ROC (AUC = {auc_score:.3f})'))
            fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1],
                           mode='lines',
                           name='Random',
                           line=dict(dash='dash', color='gray')))
        
        fig.update_layout(
            title='Receiver Operating Characteristic (ROC) Curve',
            xaxis_title='False Positive Rate',
            yaxis_title='True Positive Rate',
            legend=dict(x=0.01, y=0.99),
            width=800,
            height=600
        )
        return fig
    
    except Exception as e:
        print(f"Error generating ROC curve: {e}")
        return None

def get_feature_importance(model, feature_names):
    """Generate feature importance plot and return the figure"""
    try:
        if hasattr(model, 'feature_importances_'):
            # Get feature importances
            importances = model.feature_importances_
            
            # Create a DataFrame for better visualization
            feat_imp = pd.DataFrame({
                'Feature': feature_names,
                'Importance': importances
            })
            
            # Sort by importance
            feat_imp = feat_imp.sort_values('Importance', ascending=False)
            
            # Create a plotly bar chart
            fig = px.bar(
                feat_imp.head(15),  # Top 15 features
                x='Importance',
                y='Feature',
                orientation='h',
                title='Feature Importance',
                labels={'Importance': 'Importance Score', 'Feature': 'Feature Name'},
                color='Importance',
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            fig.update_layout(
                width=800,
                height=600
            )
            return fig
        else:
            return None
    
    except Exception as e:
        print(f"Error generating feature importance: {e}")
        return None

def get_confusion_matrix(model, X_test, y_test):
    """Generate confusion matrix visualization and return the figure"""
    try:
        # Get predictions
        y_pred = model.predict(X_test)
        
        # Create confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Get class labels
        classes = np.unique(np.concatenate((y_test, y_pred)))
        
        # Create heatmap using plotly
        fig = px.imshow(
            cm,
            labels=dict(x="Predicted", y="Actual", color="Count"),
            x=classes,
            y=classes,
            text_auto=True,
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            title='Confusion Matrix',
            width=650,
            height=600
        )
        
        return fig
    
    except Exception as e:
        print(f"Error generating confusion matrix: {e}")
        return None

def generate_classification_report(model, X_test, y_test):
    """Generate classification report as HTML"""
    try:
        y_pred = model.predict(X_test)
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Convert to DataFrame for better display
        df_report = pd.DataFrame(report).transpose()
        
        # Style the DataFrame for better presentation
        styled_report = df_report.style.background_gradient(cmap='viridis', subset=['precision', 'recall', 'f1-score'])
        
        # Convert to HTML
        html = styled_report.to_html()
        return html
    
    except Exception as e:
        print(f"Error generating classification report: {e}")
        return "<p>Error generating classification report</p>"