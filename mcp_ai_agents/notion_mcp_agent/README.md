# 📑 Notion MCP Agent

A terminal-based Notion Agent for interacting with your Notion pages using natural language through the Notion MCP (Model Context Protocol) server.

## Features

- Interact with Notion pages via a command-line interface
- Perform update, insert, retrieve operations on your Notion pages
- Create and edit blocks, lists, tables, and other Notion structures
- Add comments to blocks
- Search for specific information
- Remembers conversation context for multi-turn interactions
- Session management for persistent conversations

## Prerequisites

- Python 3.9+
- A Notion account with admin permissions
- A Notion Integration token
- An OpenAI API key

## Installation

1. Clone the repository
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. Install the Notion MCP server (will be done automatically when you run the app)

## Setting Up Notion Integration

### Creating a Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Name your integration (e.g., "Notion Assistant")
4. Select the capabilities needed (Read & Write content)
5. Submit and copy your "Internal Integration Token"

### Sharing Your Notion Page with the Integration

1. Open your Notion page
2. Click the three dots (⋮) in the top-right corner of the page
3. Select "Add connections" from the dropdown menu
4. Search for your integration name in the search box
5. Click on your integration to add it to the page
6. Confirm by clicking "Confirm" in the dialog that appears

Alternatively, you can also share via the "Share" button:
1. Click "Share" in the top right
2. In the sharing dialog, search for your integration name (preceded by "@")
3. Click on your integration to add it
4. Click "Invite" to grant it access to your page

Both methods will grant your integration full access to the page and its content.

### Finding Your Notion Page ID

1. Open your Notion page in a browser
2. Copy the URL, which looks like:
   `https://www.notion.so/workspace/Your-Page-1f5b8a8ba283...`
3. The ID is the part after the last dash and before any query parameters
   Example: `1f5b8a8bad058a7e39a6`

## Configuration

You can configure the agent using environment variables:

- `NOTION_API_KEY`: Your Notion Integration token
- `OPENAI_API_KEY`: Your OpenAI API key
- `NOTION_PAGE_ID`: The ID of your Notion page

Alternatively, you can set these values directly in the script.

## Usage

Run the agent from the command line:

```bash
python notion_mcp_agent.py
```

When you start the agent, it will prompt you to enter your Notion page ID. You can:
1. Enter your page ID at the prompt
2. Press Enter without typing anything to use the default page ID (if set)
3. Provide the page ID directly as a command-line argument (bypassing the prompt):

```bash
python notion_mcp_agent.py your-page-id-here
```

### Conversation Flow

Each time you start the agent, it creates a unique user ID and session ID to maintain conversation context. This allows the agent to remember previous interactions and continue coherent conversations even after you close and restart the application.

You can exit the conversation at any time by typing `exit`, `quit`, `bye`, or `goodbye`.

## Example Queries

- "What's on my Notion page?"
- "Add a new paragraph saying 'Meeting notes for today'"
- "Create a bullet list with three items: Apple, Banana, Orange"
- "Add a comment to the first paragraph saying 'This looks good!'"
- "Search for any mentions of meetings"
- "Summarize our conversation so far"

## License

MIT