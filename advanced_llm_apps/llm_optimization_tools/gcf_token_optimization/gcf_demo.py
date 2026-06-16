"""
GCF Token Optimization Demo

Demonstrates how GCF (Graph Compact Format) reduces token usage
when passing structured data to LLMs. Compares JSON vs GCF encoding
with real tiktoken counts.
"""

import json
import tiktoken

# Sample data: 10 e-commerce orders with nested structure
ORDERS = [
    {"id": 1001, "customer": "Acme Corp", "total": 49.99, "status": "shipped", "items": 1},
    {"id": 1002, "customer": "Globex Inc", "total": 150.49, "status": "pending", "items": 2},
    {"id": 1003, "customer": "Initech LLC", "total": 250.99, "status": "processing", "items": 3},
    {"id": 1004, "customer": "Umbrella Co", "total": 351.49, "status": "delivered", "items": 4},
    {"id": 1005, "customer": "Stark Ind", "total": 451.99, "status": "shipped", "items": 5},
    {"id": 1006, "customer": "Wayne Ent", "total": 552.49, "status": "pending", "items": 6},
    {"id": 1007, "customer": "Oscorp", "total": 652.99, "status": "shipped", "items": 7},
    {"id": 1008, "customer": "LexCorp", "total": 753.49, "status": "processing", "items": 8},
    {"id": 1009, "customer": "Cyberdyne", "total": 853.99, "status": "delivered", "items": 9},
    {"id": 1010, "customer": "Soylent", "total": 954.49, "status": "shipped", "items": 10},
]


def encode_gcf(orders: list[dict]) -> str:
    """Encode orders as GCF generic profile."""
    fields = list(orders[0].keys())
    lines = [
        "GCF profile=generic",
        f"## orders [{len(orders)}]{{{','.join(fields)}}}",
    ]
    for order in orders:
        lines.append("|".join(str(order[f]) for f in fields))
    return "\n".join(lines)


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens using tiktoken."""
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def main():
    # Encode both formats
    json_str = json.dumps({"orders": ORDERS}, indent=2)
    gcf_str = encode_gcf(ORDERS)

    # Count tokens
    json_tokens = count_tokens(json_str)
    gcf_tokens = count_tokens(gcf_str)
    reduction = (1 - gcf_tokens / json_tokens) * 100

    # Display comparison
    print("=" * 60)
    print("GCF Token Optimization Demo")
    print("=" * 60)

    print(f"\n--- JSON ({json_tokens} tokens, {len(json_str)} bytes) ---")
    print(json_str[:300] + "\n  ..." if len(json_str) > 300 else json_str)

    print(f"\n--- GCF ({gcf_tokens} tokens, {len(gcf_str)} bytes) ---")
    print(gcf_str)

    print(f"\n{'=' * 60}")
    print(f"JSON:      {json_tokens} tokens  |  {len(json_str)} bytes")
    print(f"GCF:       {gcf_tokens} tokens  |  {len(gcf_str)} bytes")
    print(f"Savings:   {reduction:.1f}% fewer tokens")
    print(f"{'=' * 60}")

    # Scale projections
    print("\nProjected savings at scale:")
    for n in [100, 500, 1000]:
        scale = json_tokens * (n / 10)
        gcf_scale = gcf_tokens * (n / 10)
        print(f"  {n:>5} rows: JSON ~{scale:.0f} tokens, GCF ~{gcf_scale:.0f} tokens ({(1 - gcf_scale/scale)*100:.0f}% savings)")


if __name__ == "__main__":
    main()
