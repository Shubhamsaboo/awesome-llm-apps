# 🎯 GCF Token Optimization

Reduce LLM API costs by 61-71% using [GCF (Graph Compact Format)](https://gcformat.com) for structured data in LLM tool responses.

## Overview

GCF is a token-optimized wire format that encodes any structured data (JSON, YAML, TOML, CSV, MessagePack) into a compact representation that LLMs read at 100% accuracy. Unlike JSON-only compressors, GCF is a universal pivot for all structured formats.

### Key Numbers

- **61-71% token reduction** vs JSON (verified with tiktoken)
- **100% comprehension accuracy** on every frontier model (1,700+ evaluations)
- **33 billion+ lossless round-trips** across 5 formats and 6 languages
- **Six implementations**: Go, Rust, TypeScript, Python, Swift, Kotlin

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Token Comparison Demo

```bash
python gcf_demo.py
```

Output:
```
============================================================
GCF Token Optimization Demo
============================================================

--- JSON (458 tokens, 809 bytes) ---
{
  "orders": [
    { "id": 1001, "customer": "Acme Corp", ... }
    ...
  ]
}

--- GCF (177 tokens, 355 bytes) ---
GCF profile=generic
## orders [10]{id,customer,total,status,items}
1001|Acme Corp|49.99|shipped|1
1002|Globex Inc|150.49|pending|2
...

============================================================
JSON:      458 tokens  |  809 bytes
GCF:       177 tokens  |  355 bytes
Savings:   61.4% fewer tokens
============================================================
```

### LLM Integration Example

```bash
export OPENAI_API_KEY='your-key'
python gcf_llm_example.py
```

Both JSON and GCF produce identical answers. GCF uses 61% fewer input tokens.

## Format Comparison

### JSON (458 tokens)
```json
{
  "orders": [
    {"id": 1001, "customer": "Acme Corp",
     "total": 49.99, "status": "shipped", "items": 1},
    {"id": 1002, "customer": "Globex Inc",
     "total": 150.49, "status": "pending", "items": 2},
    ...
  ]
}
```

### GCF (177 tokens)
```
GCF profile=generic
## orders [10]{id,customer,total,status,items}
1001|Acme Corp|49.99|shipped|1
1002|Globex Inc|150.49|pending|2
1003|Initech LLC|250.99|processing|3
...
```

Fields declared once in the header. Rows are positional. No braces, no quotes, no repeated keys.

## Why GCF over TOON?

| | GCF | TOON |
|---|---|---|
| Token savings | 61-71% | 30-60% |
| LLM comprehension | 100% (every frontier model) | 76.4% (4 models) |
| Input formats | JSON, YAML, TOML, CSV, MessagePack | JSON only |
| Round-trip verification | 33 billion+ | None published |
| Implementations | 6 languages | JavaScript |
| Graph data | Native edges, IDs, session dedup | No support |

## Zero-Code Option

Don't want to change code? Use the drop-in proxy:

```bash
pip install gcf-proxy
gcf-proxy --port 8080 --target http://localhost:3000
```

All MCP tool responses are automatically compressed. No code changes to your server or client.

## Resources

- **Website**: https://gcformat.com
- **Spec**: https://gcformat.com/reference/spec.html
- **Benchmarks**: https://gcformat.com/guide/benchmarks.html
- **GitHub**: https://github.com/blackwell-systems/gcf
- **Proxy**: https://github.com/blackwell-systems/gcf-proxy

## License

MIT
