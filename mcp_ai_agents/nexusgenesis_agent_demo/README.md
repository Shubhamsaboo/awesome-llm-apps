# NexusGenesis Agent Demo

**Post-quantum self-custody keys for AI agents — with human takeover.**

This demo shows how an AI agent can generate a CRYSTALS-Dilithium2 (NIST FIPS 204) keypair, sign a task claim message, and verify the signature — all locally, without any server dependency.

```bash
cd mcp_ai_agents/nexusgenesis_agent_demo
npm install
npm start
```

For the optional LLM audit step, pass an OpenAI key:

```bash
OPENAI_API_KEY=sk-... npm start
```

## What it demonstrates

1. **PQC Key Generation** — CRYSTALS-Dilithium2 keypair for agent identity
2. **Signing** — Agent signs a task claim message with its private key (key never leaves the caller)
3. **Verification** — Signature verified locally, no server required
4. **LLM Verification (optional)** — GPT-4o-mini explains why self-custody + human takeover matters
5. **Human Takeover** — The architecture ensures a human can always regain control from an agent

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Agent Process                      │
│  ┌───────────────────────────────────────────────┐  │
│  │  nexusgenesis-agent-keys (npm)                │  │
│  │  • Key generation (Dilithium2)                │  │
│  │  • Signing (private key never leaves process) │  │
│  │  • Verification (local, no server)            │  │
│  └───────────────────────────────────────────────┘  │
│                         │                            │
│                         ▼                            │
│  ┌───────────────────────────────────────────────┐  │
│  │  Optional: LLM audit (GPT-4o-mini)            │  │
│  │  ⚠️ Not part of the signing flow              │  │
│  │  Only reads the signed message for display    │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

> **Important:** The LLM step is purely for demonstration. It does **not** participate in the signing or verification process. The signing flow is entirely local and deterministic — no API key required.

## Why NexusGenesis vs existing solutions?

| Feature | NexusGenesis | Lit Protocol | Turnkey | Web3Auth |
|---------|-------------|-------------|---------|---------|
| **Cryptography** | CRYSTALS-Dilithium2 (PQC, FIPS 204) | BLS / ECDSA (not PQC) | ECDSA (not PQC) | ECDSA (not PQC) |
| **Key custody** | Self-custody (private key in agent process) | MPC (key shards across nodes) | HSM-backed (server-side) | MPC / social (server-side) |
| **Server dependency** | Relay only (no key material on server) | Full node network | Full server-side | Full server-side |
| **Quantum-resistant** | Yes (Dilithium2) | No | No | No |
| **Agent-native** | Built for AI agent workflows | Smart contract focused | Wallet / custody focused | Wallet / auth focused |
| **MCP protocol** | Native MCP integration | No | No | No |
| **Self-hosted** | Yes (single npm package) | No (needs Lit network) | No | No |
| **Human takeover** | Built-in (key recovery/separation) | Contract-level only | Not applicable | Not applicable |
| **Open source** | Apache 2.0 | Some components | No | No |

> **Bottom line:** NexusGenesis is the only solution that combines **post-quantum cryptography**, **self-custody keys in the agent process**, **MCP-native protocol integration**, and **self-hosted deployment** — all in a single npm package.

## How it works

The demo uses the [`nexusgenesis-agent-keys`](https://www.npmjs.com/package/nexusgenesis-agent-keys) npm package, which provides the minimal core:

- **Key generation** — Creates a Dilithium2 keypair
- **Signing** — Signs arbitrary messages with the private key
- **Verification** — Verifies signatures with the public key

This is the **only** package shipped as open source. Enterprise features (hierarchical keys, TPM binding, sharded backup, audit logging, key rotation) are available in the commercial SDK.

## Related packages

| Package | Description | Open Source |
|---------|-------------|-------------|
| [`nexusgenesis-agent-keys`](https://www.npmjs.com/package/nexusgenesis-agent-keys) | PQC key generation, signing, verification | Yes (Apache 2.0) |
| [`nexusgenesis-agent-sdk`](https://www.npmjs.com/package/nexusgenesis-agent-sdk) | Agent framework with task/reputation protocol | Yes (Apache 2.0) |
| [`nexusgenesis-agent-mcp`](https://www.npmjs.com/package/nexusgenesis-agent-mcp) | MCP server for Claude/Cursor integration | Yes (Apache 2.0) |
| Commercial SDK | Hierarchical keys, TPM binding, backup, audit, rotation | No |

## License

Apache 2.0