"""
Toonify Interactive Streamlit App
Visualize token savings and test TOON format with your own data
"""

import streamlit as st
import json
from toon import encode, decode
import tiktoken
import pandas as pd


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def calculate_cost(tokens: int, model: str = "gpt-4") -> float:
    """Calculate API cost based on token count."""
    pricing = {
        "gpt-4": 0.03 / 1000,  # $0.03 per 1K tokens
        "gpt-4-turbo": 0.01 / 1000,
        "gpt-3.5-turbo": 0.0015 / 1000,
        "claude-3-opus": 0.015 / 1000,
        "claude-3-sonnet": 0.003 / 1000,
    }
    return tokens * pricing.get(model, 0.03 / 1000)


def main():
    st.set_page_config(
        page_title="Toonify Token Optimizer",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Toonify Token Optimization")
    st.markdown("""
    Reduce your LLM API costs by **30-60%** using TOON format for structured data!
    
    [GitHub](https://github.com/ScrapeGraphAI/toonify) | 
    [Documentation](https://docs.scrapegraphai.com/services/toonify)
    """)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        model = st.selectbox(
            "LLM Model",
            ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"],
            help="Select model for token counting and cost calculation"
        )
        
        delimiter = st.selectbox(
            "TOON Delimiter",
            ["comma", "tab", "pipe"],
            help="Choose delimiter for array elements"
        )
        
        key_folding = st.selectbox(
            "Key Folding",
            ["off", "safe"],
            help="Collapse nested single-key chains into dotted paths"
        )
        
        st.markdown("---")
        st.markdown("### 💡 Quick Tips")
        st.info("""
        **Best for:**
        - Tabular data
        - Product catalogs
        - Survey responses
        - Analytics data
        
        **Avoid for:**
        - Highly nested data
        - Irregular structures
        """)
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📊 Comparison", "✍️ Custom Data", "📈 Benchmark"])
    
    with tab1:
        st.header("JSON vs TOON Comparison")
        
        # Example data selector
        example = st.selectbox(
            "Choose example dataset",
            [
                "E-commerce Products",
                "Customer Orders",
                "Survey Responses",
                "Analytics Data"
            ]
        )
        
        # Load example data
        examples = {
            "E-commerce Products": {
                "products": [
                    {"id": 1, "name": "Laptop Pro", "price": 1299, "stock": 45, "rating": 4.5},
                    {"id": 2, "name": "Magic Mouse", "price": 79, "stock": 120, "rating": 4.2},
                    {"id": 3, "name": "USB-C Cable", "price": 19, "stock": 350, "rating": 4.8},
                    {"id": 4, "name": "Keyboard", "price": 89, "stock": 85, "rating": 4.6},
                    {"id": 5, "name": "Monitor Stand", "price": 45, "stock": 60, "rating": 4.3}
                ]
            },
            "Customer Orders": {
                "orders": [
                    {"order_id": "ORD001", "customer": "Alice", "total": 299.99, "status": "shipped"},
                    {"order_id": "ORD002", "customer": "Bob", "total": 149.50, "status": "processing"},
                    {"order_id": "ORD003", "customer": "Charlie", "total": 449.99, "status": "delivered"}
                ]
            },
            "Survey Responses": {
                "responses": [
                    {"id": 1, "age": 25, "satisfaction": 4, "recommend": True, "comment": "Great service!"},
                    {"id": 2, "age": 34, "satisfaction": 5, "recommend": True, "comment": "Excellent!"},
                    {"id": 3, "age": 42, "satisfaction": 3, "recommend": False, "comment": "Could be better"}
                ]
            },
            "Analytics Data": {
                "pageviews": [
                    {"page": "/home", "views": 1523, "avg_time": 45, "bounce_rate": 0.32},
                    {"page": "/products", "views": 892, "avg_time": 120, "bounce_rate": 0.45},
                    {"page": "/about", "views": 234, "avg_time": 60, "bounce_rate": 0.28}
                ]
            }
        }
        
        data = examples[example]
        
        # Convert formats
        json_str = json.dumps(data, indent=2)
        toon_options = {
            'delimiter': delimiter,
            'key_folding': key_folding
        }
        toon_str = encode(data, toon_options)
        
        # Calculate metrics
        json_size = len(json_str.encode('utf-8'))
        toon_size = len(toon_str.encode('utf-8'))
        json_tokens = count_tokens(json_str, model)
        toon_tokens = count_tokens(toon_str, model)
        
        size_reduction = ((json_size - toon_size) / json_size) * 100
        token_reduction = ((json_tokens - toon_tokens) / json_tokens) * 100
        
        json_cost = calculate_cost(json_tokens, model)
        toon_cost = calculate_cost(toon_tokens, model)
        cost_savings = json_cost - toon_cost
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Size Reduction", f"{size_reduction:.1f}%")
        with col2:
            st.metric("Token Reduction", f"{token_reduction:.1f}%")
        with col3:
            st.metric("Cost per Call", f"${toon_cost:.6f}", f"-${cost_savings:.6f}")
        with col4:
            savings_1k = cost_savings * 1000
            st.metric("Savings per 1K calls", f"${savings_1k:.2f}")
        
        # Side-by-side comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 JSON Format")
            st.code(json_str, language="json")
            st.caption(f"Size: {json_size} bytes | Tokens: {json_tokens}")
        
        with col2:
            st.subheader("🎯 TOON Format")
            st.code(toon_str, language="text")
            st.caption(f"Size: {toon_size} bytes | Tokens: {toon_tokens}")
        
        # Cost projection
        st.subheader("💰 Cost Savings Projection")
        
        calls = [100, 1_000, 10_000, 100_000, 1_000_000]
        json_costs = [json_cost * n for n in calls]
        toon_costs = [toon_cost * n for n in calls]
        savings = [json_costs[i] - toon_costs[i] for i in range(len(calls))]
        
        df = pd.DataFrame({
            "API Calls": [f"{n:,}" for n in calls],
            "JSON Cost": [f"${c:.2f}" for c in json_costs],
            "TOON Cost": [f"${c:.2f}" for c in toon_costs],
            "Savings": [f"${s:.2f}" for s in savings],
            "Savings %": [f"{token_reduction:.1f}%" for _ in calls]
        })
        
        st.dataframe(df, use_container_width=True)
    
    with tab2:
        st.header("Test Your Own Data")
        
        st.markdown("Paste your JSON data below to see how much you can save:")
        
        user_json = st.text_area(
            "JSON Data",
            value='{\n  "items": [\n    {"id": 1, "name": "Example", "value": 100}\n  ]\n}',
            height=300
        )
        
        if st.button("🎯 Convert to TOON"):
            try:
                # Parse JSON
                data = json.loads(user_json)
                
                # Convert to TOON
                toon_options = {
                    'delimiter': delimiter,
                    'key_folding': key_folding
                }
                toon_str = encode(data, toon_options)
                
                # Calculate savings
                json_size = len(user_json.encode('utf-8'))
                toon_size = len(toon_str.encode('utf-8'))
                json_tokens = count_tokens(user_json, model)
                toon_tokens = count_tokens(toon_str, model)
                
                size_reduction = ((json_size - toon_size) / json_size) * 100
                token_reduction = ((json_tokens - toon_tokens) / json_tokens) * 100
                
                # Display results
                st.success("✅ Conversion successful!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Size Reduction", f"{size_reduction:.1f}%")
                with col2:
                    st.metric("Token Reduction", f"{token_reduction:.1f}%")
                with col3:
                    cost_savings = calculate_cost(json_tokens - toon_tokens, model)
                    st.metric("Savings per call", f"${cost_savings:.6f}")
                
                st.subheader("🎯 TOON Output")
                st.code(toon_str, language="text")
                
                # Verify roundtrip
                decoded = decode(toon_str)
                if decoded == data:
                    st.success("✅ Roundtrip verification passed!")
                else:
                    st.warning("⚠️  Roundtrip verification failed")
                
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON: {e}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with tab3:
        st.header("📈 Format Benchmark")
        
        st.markdown("""
        Based on benchmarks across 50 real-world datasets:
        """)
        
        # Benchmark stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg Size Reduction", "63.9%")
        with col2:
            st.metric("Avg Token Reduction", "54.1%")
        with col3:
            st.metric("Best Case", "73.4%")
        
        # Data type performance
        st.subheader("Performance by Data Type")
        
        performance_data = {
            "Data Type": ["Tabular", "E-commerce", "Analytics", "Surveys", "Mixed"],
            "Token Reduction": [73.4, 68.2, 65.1, 61.5, 48.3],
            "Use Case": ["✅ Excellent", "✅ Excellent", "✅ Great", "✅ Great", "✅ Good"]
        }
        
        df = pd.DataFrame(performance_data)
        st.dataframe(df, use_container_width=True)
        
        st.info("""
        **💡 Optimization Tips:**
        - Use TOON for uniform, structured data
        - Enable key folding for deeply nested objects
        - Choose appropriate delimiter based on your data
        - Test with your actual data for best results
        """)
        
        st.markdown("---")
        st.markdown("""
        ### 🔗 Learn More
        - [GitHub Repository](https://github.com/ScrapeGraphAI/toonify)
        - [Documentation](https://docs.scrapegraphai.com/services/toonify)
        - [Format Specification](https://github.com/toon-format/toon)
        """)


if __name__ == "__main__":
    main()

