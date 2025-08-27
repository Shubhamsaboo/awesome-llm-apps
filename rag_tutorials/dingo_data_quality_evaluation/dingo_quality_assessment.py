"""
Dingo Data Quality Evaluation App

This application demonstrates how to use Dingo for comprehensive data quality assessment
including rule-based evaluation, LLM-based assessment, and hallucination detection.

Features:
- Multi-dimensional data quality evaluation
- Rule-based and LLM-based assessment
- Hallucination detection for RAG systems
- Support for various data sources and formats
- Comprehensive reporting and visualization
"""

import streamlit as st
import pandas as pd
import json
import tempfile
import os
from datetime import datetime
from typing import List, Dict, Any
import plotly.express as px
import plotly.graph_objects as go

# Note: In a real implementation, you would install and import the actual Dingo package
# For this demo, we'll simulate the Dingo functionality

class DingoSimulator:
    """
    Simulates Dingo functionality for demonstration purposes.
    In actual implementation, you would use: from dingo import Executor, InputArgs
    """
    
    def __init__(self):
        self.rules = {
            'QUALITY_BAD_COMPLETENESS': 'Check for incomplete content',
            'QUALITY_BAD_RELEVANCE': 'Check for irrelevant content', 
            'QUALITY_BAD_SIMILARITY': 'Check for duplicate content',
            'QUALITY_BAD_COHERENCE': 'Check for coherent structure',
            'QUALITY_BAD_CONSISTENCY': 'Check for consistency',
            'QUALITY_BAD_FLUENCY': 'Check for language fluency',
            'QUALITY_BAD_FACTUALITY': 'Check for factual accuracy'
        }
        
        self.eval_groups = {
            'default': 'General text quality evaluation',
            'sft': 'Supervised fine-tuning dataset evaluation',
            'rag': 'RAG system evaluation with hallucination detection',
            'hallucination': 'Specialized hallucination detection',
            'pretrain': 'Pre-training dataset evaluation'
        }
    
    def evaluate_data(self, data: List[Dict], eval_group: str = 'default', 
                     llm_model: str = None) -> Dict[str, Any]:
        """Simulate data quality evaluation"""
        import random
        
        total_samples = len(data)
        
        # Simulate evaluation results
        good_samples = random.randint(int(total_samples * 0.6), int(total_samples * 0.9))
        bad_samples = total_samples - good_samples
        
        # Generate type ratios
        type_ratio = {}
        remaining_bad = bad_samples
        
        for rule_type in list(self.rules.keys())[:3]:  # Use first 3 rules
            if remaining_bad > 0:
                ratio = random.uniform(0.1, 0.3) if remaining_bad > 1 else remaining_bad / total_samples
                type_ratio[rule_type] = min(ratio, remaining_bad / total_samples)
                remaining_bad -= int(ratio * total_samples)
        
        # Generate detailed results
        results = {
            'task_id': f"dingo_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'task_name': 'dingo_quality_evaluation',
            'eval_group': eval_group,
            'create_time': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'score': round((good_samples / total_samples) * 100, 2),
            'num_good': good_samples,
            'num_bad': bad_samples,
            'total': total_samples,
            'type_ratio': type_ratio,
            'llm_model': llm_model,
            'quality_dimensions': {
                'completeness': random.uniform(0.7, 0.95),
                'relevance': random.uniform(0.6, 0.9),
                'coherence': random.uniform(0.7, 0.92),
                'consistency': random.uniform(0.65, 0.88),
                'fluency': random.uniform(0.8, 0.95),
                'factuality': random.uniform(0.6, 0.85),
                'similarity': random.uniform(0.7, 0.9)
            }
        }
        
        return results

def main():
    st.set_page_config(
        page_title="Dingo Data Quality Evaluation",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Dingo Data Quality Evaluation")
    st.markdown("Comprehensive AI Data Quality Assessment Tool")
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    # Evaluation group selection
    eval_group = st.sidebar.selectbox(
        "Select Evaluation Group",
        options=['default', 'sft', 'rag', 'hallucination', 'pretrain'],
        help="Choose the appropriate evaluation group for your data type"
    )
    
    # LLM model selection for advanced evaluation
    use_llm = st.sidebar.checkbox("Use LLM-based Evaluation", value=False)
    llm_model = None
    
    if use_llm:
        llm_model = st.sidebar.selectbox(
            "Select LLM Model",
            options=['gpt-4o', 'gpt-3.5-turbo', 'claude-3-sonnet', 'llama-3-8b'],
            help="Choose LLM model for quality assessment"
        )
        
        st.sidebar.text_input(
            "API Key",
            type="password",
            help="Enter your LLM API key"
        )
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["Data Input", "Evaluation Results", "Quality Insights"])
    
    with tab1:
        st.header("Data Input")
        
        # Data source selection
        data_source = st.radio(
            "Select Data Source",
            options=["Upload File", "Text Input", "Sample Data"],
            horizontal=True
        )
        
        data = []
        
        if data_source == "Upload File":
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['json', 'jsonl', 'csv', 'txt'],
                help="Upload your dataset file"
            )
            
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                        data = df.to_dict('records')
                    elif uploaded_file.name.endswith('.json'):
                        data = json.load(uploaded_file)
                    elif uploaded_file.name.endswith('.jsonl'):
                        lines = uploaded_file.read().decode().strip().split('\n')
                        data = [json.loads(line) for line in lines if line.strip()]
                    else:
                        content = uploaded_file.read().decode()
                        data = [{"text": line} for line in content.split('\n') if line.strip()]
                    
                    st.success(f"Loaded {len(data)} samples")
                    
                except Exception as e:
                    st.error(f"Error loading file: {str(e)}")
        
        elif data_source == "Text Input":
            text_input = st.text_area(
                "Enter your text data (one sample per line)",
                height=200,
                help="Enter text data, one sample per line"
            )
            
            if text_input.strip():
                lines = [line.strip() for line in text_input.split('\n') if line.strip()]
                data = [{"text": line} for line in lines]
                st.success(f"Prepared {len(data)} samples")
        
        else:  # Sample Data
            data = [
                {"text": "This is a high-quality, complete sentence with proper grammar."},
                {"text": "incomplete sentence without"},
                {"text": "This sentence contains factual information about Paris being the capital of France."},
                {"text": "Random symbols: @@##$$ without context or meaning."},
                {"text": "A well-structured paragraph that flows logically and maintains coherence throughout its content."},
                {"text": ""},  # Empty content
                {"text": "Repeated content. Repeated content. Repeated content."},
                {"text": "Technical documentation should be clear, concise, and comprehensive for users."}
            ]
            st.info(f"Using {len(data)} sample records for demonstration")
        
        # Display data preview
        if data:
            st.subheader("Data Preview")
            df_preview = pd.DataFrame(data[:10])  # Show first 10 samples
            st.dataframe(df_preview, use_container_width=True)
    
    with tab2:
        st.header("Evaluation Results")
        
        if data and st.button("Run Quality Evaluation", type="primary"):
            with st.spinner("Running Dingo evaluation..."):
                # Initialize Dingo simulator
                dingo = DingoSimulator()
                
                # Run evaluation
                results = dingo.evaluate_data(data, eval_group, llm_model)
                
                # Store results in session state
                st.session_state.results = results
                
            st.success("Evaluation completed!")
        
        # Display results if available
        if hasattr(st.session_state, 'results'):
            results = st.session_state.results
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Overall Score", f"{results['score']}%")
            
            with col2:
                st.metric("Good Samples", results['num_good'])
            
            with col3:
                st.metric("Bad Samples", results['num_bad'])
            
            with col4:
                st.metric("Total Samples", results['total'])
            
            # Quality dimensions chart
            st.subheader("Quality Dimensions")
            
            dimensions = results['quality_dimensions']
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=list(dimensions.values()),
                theta=list(dimensions.keys()),
                fill='toself',
                name='Quality Score'
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )),
                showlegend=True,
                title="Data Quality Dimensions"
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
            
            # Issue distribution
            if results['type_ratio']:
                st.subheader("Quality Issues Distribution")
                
                issue_data = pd.DataFrame([
                    {"Issue Type": k, "Ratio": v} 
                    for k, v in results['type_ratio'].items()
                ])
                
                fig_bar = px.bar(
                    issue_data, 
                    x="Issue Type", 
                    y="Ratio",
                    title="Distribution of Quality Issues"
                )
                
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # Detailed results
            st.subheader("Detailed Results")
            results_df = pd.DataFrame([results])
            st.dataframe(results_df, use_container_width=True)
            
            # Download results
            results_json = json.dumps(results, indent=2)
            st.download_button(
                label="Download Results (JSON)",
                data=results_json,
                file_name=f"dingo_results_{results['task_id']}.json",
                mime="application/json"
            )
    
    with tab3:
        st.header("Quality Insights & Recommendations")
        
        if hasattr(st.session_state, 'results'):
            results = st.session_state.results
            
            st.subheader("📊 Quality Analysis")
            
            # Overall assessment
            score = results['score']
            if score >= 80:
                st.success(f"✅ Excellent data quality ({score}%)")
                st.write("Your dataset demonstrates high quality across multiple dimensions.")
            elif score >= 60:
                st.warning(f"⚠️ Good data quality with room for improvement ({score}%)")
                st.write("Your dataset shows decent quality but could benefit from some improvements.")
            else:
                st.error(f"❌ Poor data quality requires attention ({score}%)")
                st.write("Your dataset has significant quality issues that should be addressed.")
            
            # Specific recommendations
            st.subheader("🎯 Recommendations")
            
            dimensions = results['quality_dimensions']
            recommendations = []
            
            if dimensions['completeness'] < 0.8:
                recommendations.append("• **Completeness**: Review and complete partial or truncated samples")
            
            if dimensions['relevance'] < 0.8:
                recommendations.append("• **Relevance**: Remove or improve samples that don't match your use case")
            
            if dimensions['coherence'] < 0.8:
                recommendations.append("• **Coherence**: Improve logical flow and structure of content")
            
            if dimensions['factuality'] < 0.8:
                recommendations.append("• **Factuality**: Verify and correct factual information")
            
            if dimensions['fluency'] < 0.8:
                recommendations.append("• **Fluency**: Fix grammatical errors and improve language quality")
            
            if recommendations:
                st.write("**Priority improvements:**")
                for rec in recommendations:
                    st.write(rec)
            else:
                st.write("🎉 Your data meets quality standards across all dimensions!")
            
            # Best practices
            st.subheader("💡 Best Practices")
            st.write("""
            **Data Quality Best Practices:**
            
            1. **Regular Evaluation**: Run quality assessments regularly during data preparation
            2. **Multi-dimensional Assessment**: Consider all quality dimensions, not just one metric
            3. **Domain-specific Rules**: Use appropriate evaluation groups (SFT, RAG, etc.)
            4. **LLM Integration**: Combine rule-based and LLM-based evaluation for comprehensive assessment
            5. **Iterative Improvement**: Use results to guide data cleaning and improvement efforts
            6. **Documentation**: Maintain records of quality metrics and improvement actions
            """)
        
        else:
            st.info("Run an evaluation to see quality insights and recommendations.")

if __name__ == "__main__":
    main()
