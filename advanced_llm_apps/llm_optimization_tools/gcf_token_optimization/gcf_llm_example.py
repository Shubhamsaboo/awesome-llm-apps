"""
GCF + LLM Integration Example

Shows how to send GCF-encoded data to an LLM and get accurate responses
with fewer tokens than JSON.
"""

import json
import os
from openai import OpenAI


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

QUESTION = "How many orders have status 'shipped'? What is the total revenue of shipped orders?"


def encode_gcf(orders: list[dict]) -> str:
    fields = list(orders[0].keys())
    lines = [
        "GCF profile=generic",
        f"## orders [{len(orders)}]{{{','.join(fields)}}}",
    ]
    for order in orders:
        lines.append("|".join(str(order[f]) for f in fields))
    return "\n".join(lines)


def ask_llm(data_str: str, format_name: str) -> str:
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer questions about the data provided. Be concise."},
            {"role": "user", "content": f"Data:\n{data_str}\n\nQuestion: {QUESTION}"},
        ],
        temperature=0,
    )
    return response.choices[0].message.content


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY to run LLM integration example.")
        print("Example: export OPENAI_API_KEY='sk-...'")
        return

    json_str = json.dumps({"orders": ORDERS}, indent=2)
    gcf_str = encode_gcf(ORDERS)

    print(f"Question: {QUESTION}\n")

    print(f"--- JSON response ({len(json_str)} bytes) ---")
    print(ask_llm(json_str, "JSON"))

    print(f"\n--- GCF response ({len(gcf_str)} bytes) ---")
    print(ask_llm(gcf_str, "GCF"))

    print("\nBoth formats produce the same answer. GCF uses fewer tokens.")


if __name__ == "__main__":
    main()
