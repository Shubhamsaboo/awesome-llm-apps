"""
Toonify Token Optimization Demo
Demonstrates how to reduce LLM API costs by 30-60% using TOON format
"""

import json
from toon import encode, decode
import tiktoken
from openai import OpenAI
from anthropic import Anthropic
import os


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def format_comparison_demo():
    """Compare JSON vs TOON format sizes and token counts."""
    
    print("=" * 80)
    print("🎯 TOONIFY TOKEN OPTIMIZATION DEMO")
    print("=" * 80)
    
    # Example: E-commerce product catalog
    products_data = {
        "products": [
            {
                "id": 101,
                "name": "Laptop Pro 15",
                "category": "Electronics",
                "price": 1299.99,
                "stock": 45,
                "rating": 4.5
            },
            {
                "id": 102,
                "name": "Magic Mouse",
                "category": "Electronics",
                "price": 79.99,
                "stock": 120,
                "rating": 4.2
            },
            {
                "id": 103,
                "name": "USB-C Cable",
                "category": "Accessories",
                "price": 19.99,
                "stock": 350,
                "rating": 4.8
            },
            {
                "id": 104,
                "name": "Wireless Keyboard",
                "category": "Electronics",
                "price": 89.99,
                "stock": 85,
                "rating": 4.6
            },
            {
                "id": 105,
                "name": "Monitor Stand",
                "category": "Accessories",
                "price": 45.99,
                "stock": 60,
                "rating": 4.3
            }
        ]
    }
    
    # Convert to JSON
    json_str = json.dumps(products_data, indent=2)
    json_size = len(json_str.encode('utf-8'))
    json_tokens = count_tokens(json_str)
    
    # Convert to TOON
    toon_str = encode(products_data)
    toon_size = len(toon_str.encode('utf-8'))
    toon_tokens = count_tokens(toon_str)
    
    # Calculate savings
    size_reduction = ((json_size - toon_size) / json_size) * 100
    token_reduction = ((json_tokens - toon_tokens) / json_tokens) * 100
    
    print("\n📊 FORMAT COMPARISON")
    print("-" * 80)
    
    print("\n📄 JSON Format:")
    print(json_str)
    print(f"\nSize: {json_size} bytes")
    print(f"Tokens: {json_tokens}")
    
    print("\n" + "=" * 80)
    
    print("\n🎯 TOON Format:")
    print(toon_str)
    print(f"\nSize: {toon_size} bytes")
    print(f"Tokens: {toon_tokens}")
    
    print("\n" + "=" * 80)
    print("\n💰 SAVINGS")
    print("-" * 80)
    print(f"Size Reduction: {size_reduction:.1f}%")
    print(f"Token Reduction: {token_reduction:.1f}%")
    
    # Calculate cost savings
    # GPT-4 pricing: $0.03 per 1K tokens (input)
    cost_per_token = 0.03 / 1000
    json_cost = json_tokens * cost_per_token
    toon_cost = toon_tokens * cost_per_token
    savings_per_call = json_cost - toon_cost
    
    print(f"\n💵 Cost per API call:")
    print(f"  JSON: ${json_cost:.6f}")
    print(f"  TOON: ${toon_cost:.6f}")
    print(f"  Savings: ${savings_per_call:.6f} ({token_reduction:.1f}%)")
    
    print(f"\n📈 Projected savings:")
    print(f"  Per 1,000 calls: ${savings_per_call * 1000:.2f}")
    print(f"  Per 1M calls: ${savings_per_call * 1_000_000:.2f}")
    
    print("\n" + "=" * 80)
    
    return toon_str, products_data


def llm_integration_demo():
    """Demonstrate using TOON format with LLM APIs."""
    
    print("\n🤖 LLM INTEGRATION DEMO")
    print("=" * 80)
    
    # Create sample data
    customer_orders = {
        "orders": [
            {"order_id": "ORD001", "customer": "Alice", "total": 299.99, "status": "shipped"},
            {"order_id": "ORD002", "customer": "Bob", "total": 149.50, "status": "processing"},
            {"order_id": "ORD003", "customer": "Charlie", "total": 449.99, "status": "delivered"},
            {"order_id": "ORD004", "customer": "Diana", "total": 89.99, "status": "pending"},
        ]
    }
    
    # Convert to TOON
    toon_data = encode(customer_orders)
    json_data = json.dumps(customer_orders, indent=2)
    
    print("\n📦 Data to analyze:")
    print(toon_data)
    
    # Check if API keys are available
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if openai_key:
        try:
            print("\n🔵 Testing with OpenAI GPT-4...")
            client = OpenAI(api_key=openai_key)
            
            prompt = f"""Analyze these customer orders and provide a brief summary:

{toon_data}

Provide: 1) Total revenue, 2) Orders by status, 3) Average order value"""
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            
            print("\n✅ GPT-4 Response:")
            print(response.choices[0].message.content)
            
            # Show token usage
            print(f"\n📊 Token Usage:")
            print(f"  Input tokens: {response.usage.prompt_tokens}")
            print(f"  Output tokens: {response.usage.completion_tokens}")
            print(f"  Total tokens: {response.usage.total_tokens}")
            
            # Compare with JSON
            json_tokens = count_tokens(prompt.replace(toon_data, json_data))
            toon_tokens = response.usage.prompt_tokens
            savings = ((json_tokens - toon_tokens) / json_tokens) * 100
            print(f"\n💰 Token Savings: {savings:.1f}% (vs JSON)")
            
        except Exception as e:
            print(f"❌ OpenAI Error: {e}")
    else:
        print("\n⚠️  Set OPENAI_API_KEY to test with GPT-4")
    
    if anthropic_key:
        try:
            print("\n🟣 Testing with Anthropic Claude...")
            client = Anthropic(api_key=anthropic_key)
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze these customer orders and provide a brief summary:

{toon_data}

Provide: 1) Total revenue, 2) Orders by status, 3) Average order value"""
                }]
            )
            
            print("\n✅ Claude Response:")
            print(response.content[0].text)
            
            # Show token usage
            print(f"\n📊 Token Usage:")
            print(f"  Input tokens: {response.usage.input_tokens}")
            print(f"  Output tokens: {response.usage.output_tokens}")
            
        except Exception as e:
            print(f"❌ Anthropic Error: {e}")
    else:
        print("\n⚠️  Set ANTHROPIC_API_KEY to test with Claude")


def advanced_features_demo():
    """Demonstrate advanced TOON features."""
    
    print("\n⚙️  ADVANCED FEATURES")
    print("=" * 80)
    
    # Key folding example
    nested_data = {
        'api': {
            'response': {
                'product': {
                    'title': 'Wireless Keyboard',
                    'specs': {
                        'battery': '6 months',
                        'connectivity': 'Bluetooth 5.0'
                    }
                }
            }
        }
    }
    
    print("\n1️⃣  Key Folding (collapse nested paths)")
    print("-" * 80)
    
    # Without key folding
    normal_toon = encode(nested_data)
    print("Without key folding:")
    print(normal_toon)
    
    # With key folding
    folded_toon = encode(nested_data, {'key_folding': 'safe'})
    print("\nWith key folding:")
    print(folded_toon)
    
    print(f"\nSavings: {len(normal_toon)} → {len(folded_toon)} bytes")
    
    # Custom delimiters
    print("\n2️⃣  Custom Delimiters")
    print("-" * 80)
    
    data = {
        "items": [
            ["Product A", "Description with, commas", 29.99],
            ["Product B", "Another, description", 39.99]
        ]
    }
    
    print("Tab delimiter (for data with commas):")
    tab_toon = encode(data, {'delimiter': 'tab'})
    print(tab_toon)
    
    print("\nPipe delimiter:")
    pipe_toon = encode(data, {'delimiter': 'pipe'})
    print(pipe_toon)


def main():
    """Run all demos."""
    
    # Basic comparison
    toon_str, original_data = format_comparison_demo()
    
    # Verify roundtrip
    decoded_data = decode(toon_str)
    assert decoded_data == original_data, "Roundtrip failed!"
    print("\n✅ Roundtrip verification: PASSED")
    
    # LLM integration (optional, requires API keys)
    llm_integration_demo()
    
    # Advanced features
    advanced_features_demo()
    
    print("\n" + "=" * 80)
    print("🎉 Demo completed!")
    print("💡 Set OPENAI_API_KEY or ANTHROPIC_API_KEY to test LLM integration")
    print("🔗 Learn more: https://github.com/ScrapeGraphAI/toonify")
    print("=" * 80)


if __name__ == "__main__":
    main()

