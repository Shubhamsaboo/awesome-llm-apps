"""
Quick test to verify Toonify installation and basic functionality
Run this to quickly see the token savings in action!
"""

import json
from toon import encode, decode


def quick_test():
    """Quick demonstration of Toonify savings."""
    
    print("🎯 TOONIFY QUICK TEST")
    print("=" * 60)
    
    # Sample data: Product catalog
    products = {
        "products": [
            {"id": 1, "name": "Laptop", "price": 1299, "stock": 45},
            {"id": 2, "name": "Mouse", "price": 79, "stock": 120},
            {"id": 3, "name": "Keyboard", "price": 89, "stock": 85},
            {"id": 4, "name": "Monitor", "price": 399, "stock": 32},
            {"id": 5, "name": "Webcam", "price": 129, "stock": 67}
        ]
    }
    
    # Convert to JSON
    json_str = json.dumps(products, indent=2)
    json_size = len(json_str)
    
    # Convert to TOON
    toon_str = encode(products)
    toon_size = len(toon_str)
    
    # Calculate savings
    reduction = ((json_size - toon_size) / json_size) * 100
    
    # Display results
    print(f"\n📄 JSON ({json_size} bytes):")
    print(json_str)
    
    print(f"\n🎯 TOON ({toon_size} bytes):")
    print(toon_str)
    
    print(f"\n💰 Size Reduction: {reduction:.1f}%")
    print(f"   Saved: {json_size - toon_size} bytes")
    
    # Verify roundtrip
    decoded = decode(toon_str)
    if decoded == products:
        print("\n✅ Roundtrip verification: PASSED")
    else:
        print("\n❌ Roundtrip verification: FAILED")
        return False
    
    print("\n" + "=" * 60)
    print("✨ Installation verified! Run toonify_demo.py for full demo.")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = quick_test()
        exit(0 if success else 1)
    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Install dependencies with: pip install -r requirements.txt")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)

