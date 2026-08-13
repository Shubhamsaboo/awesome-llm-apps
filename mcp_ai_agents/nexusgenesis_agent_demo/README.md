# NexusGenesis Agent Demo

A self-contained example demonstrating **post-quantum (PQC) self-custody keys** for autonomous AI agents — the core of the NexusGenesis security standard.

**Key principle:** An agent's private keys should never leave the agent. And a human should always be able to take control back.

## What it shows

1. **PQC Key Generation** — Creates a CRYSTALS-Dilithium2 (NIST FIPS 204) key pair for the agent
2. **Signing** — The agent signs a message with its private key
3. **Verification** — Signature is verified locally, no server needed
4. **LLM Verification (optional)** — An LLM (GPT-4o-mini) explains why self-custody matters
5. **Human Takeover** — The architecture ensures a human can always regain control

## Quick Start

```bash
# Install dependencies
npm install

# Run the demo (basic)
npm start

# Run with LLM verification
cp .env.example .env   # then add your OPENAI_API_KEY
# or
OPENAI_API_KEY=sk-... npm start
```

## Learn More

- [nexusgenesis-agent-keys](https://www.npmjs.com/package/nexusgenesis-agent-keys) — PQC key security core
- [nexusgenesis-agent-sdk](https://www.npmjs.com/package/nexusgenesis-agent-sdk) — Agent framework with task/reputation protocol
- [nexusgenesis-agent-mcp](https://www.npmjs.com/package/nexusgenesis-agent-mcp) — MCP server for Claude/Cursor integration
- [GitHub Repo](https://github.com/nexus-genesis/nexusgenesis)