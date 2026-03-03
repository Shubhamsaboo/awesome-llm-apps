# DeFi MCP Agent

A Streamlit application that lets you query real-time DeFi data using natural language through the Model Context Protocol (MCP).

## Features

- **Token Prices**: Get real-time prices for 275+ crypto assets
- **Wallet Balances**: Check balances across 9 blockchain networks
- **Gas Prices**: Monitor gas fees on Ethereum and other chains
- **DEX Quotes**: Get swap quotes from Ethereum (1inch) and Solana (Jupiter)
- **Token Search**: Search and discover tokens by name or symbol
- **ENS Resolution**: Resolve ENS names to addresses

## Setup

### Requirements

- Python 3.8+
- Node.js 18+ (for the DeFi MCP server)
- OpenAI API Key

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/defi_mcp_agent
   ```

2. Clone the DeFi MCP server:
   ```bash
   git clone https://github.com/OzorOwn/defi-mcp.git ../defi-mcp
   cd ../defi-mcp && npm install && cd ../defi_mcp_agent
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:
   ```bash
   streamlit run defi_agent.py
   ```

5. Enter your OpenAI API key in the sidebar and start querying.

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `get_token_price` | Current price of any cryptocurrency |
| `search_tokens` | Search tokens by name or symbol |
| `get_token_info` | Detailed token info (market cap, volume) |
| `get_top_tokens` | Top tokens by market cap |
| `get_eth_balance` | ETH balance of any address/ENS name |
| `get_token_balance` | ERC-20 token balance |
| `get_wallet_holdings` | All token holdings for a wallet |
| `get_multichain_balance` | Balances across 9 chains |
| `get_eth_gas` | Current Ethereum gas prices |
| `get_multichain_gas` | Gas prices across multiple chains |
| `get_dex_quote_eth` | DEX swap quote on Ethereum |
| `get_dex_quote_sol` | DEX swap quote on Solana |
