# AI Financial Coach Agent

A multi-agent financial coach that analyzes your budget, plans your savings, and builds debt-payoff strategies — rendered as interactive UI cards in a separate report tab. Built with [CopilotKit](https://github.com/CopilotKit/CopilotKit), [AG-UI](https://github.com/ag-ui-protocol/ag-ui), and Google's [ADK](https://google.github.io/adk-docs/) on top of Next.js.

https://github.com/user-attachments/assets/edd4fa8d-ecc5-4b5d-90ff-27b21af5af94

**Gen UI concept — tool-rendered components.** A top-level coach routes each chat turn to the right tool: update your financial profile from natural language ("my income is $8k"), run a single phase (budget / savings / debt), or run the full Budget→Savings→Debt sequence. Each tool call streams a status pill into the chat while the corresponding card materializes in the report tab.

## Prerequisites

- Node.js 18+
- Python 3.12+
- Google Makersuite API Key (for the ADK agent) (see https://makersuite.google.com/app/apikey)
- Any of the following package managers:
  - npm (default)
  - [pnpm](https://pnpm.io/installation)
  - [yarn](https://classic.yarnpkg.com/lang/en/docs/install/)
  - [bun](https://bun.sh/)

## Getting Started

1. Install dependencies (npm, or pnpm/yarn/bun):

```bash
npm install
```

2. Install Python dependencies for the ADK agent:

```bash
npm run install:agent
```

> **Note:** This will automatically setup a `.venv` (virtual environment) inside the `agent` directory.
>
> To activate the virtual environment manually, you can run:
>
> ```bash
> source agent/.venv/bin/activate
> ```

3. Set up your Google API key:

```bash
export GOOGLE_API_KEY="your-google-api-key-here"
```

4. Start the development server:

```bash
npm run dev
```

This will start both the UI and agent servers concurrently.

## Available Scripts

The following scripts can also be run using your preferred package manager:

- `dev` - Starts both UI and agent servers in development mode
- `dev:debug` - Starts development servers with debug logging enabled
- `dev:ui` - Starts only the Next.js UI server
- `dev:agent` - Starts only the ADK agent server
- `build` - Builds the Next.js application for production
- `start` - Starts the production server
- `install:agent` - Installs Python dependencies for the agent

## Customization

The main UI component is in `src/app/page.tsx`. You can:

- Modify the theme colors and styling
- Add new frontend actions
- Customize the CopilotKit sidebar appearance

## 📚 Documentation

- [ADK Documentation](https://google.github.io/adk-docs/) - Learn more about the ADK and its features
- [CopilotKit Documentation](https://docs.copilotkit.ai) - Explore CopilotKit's capabilities
- [Next.js Documentation](https://nextjs.org/docs) - Learn about Next.js features and API
