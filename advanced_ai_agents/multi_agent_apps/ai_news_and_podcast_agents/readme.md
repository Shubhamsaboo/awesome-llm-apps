# 🦉 Beifong: Your Junk-Free, Personalized Information and Podcasts

![image](https://github.com/user-attachments/assets/b2f24f12-6f80-46fa-aa31-ee42e17765b1)

Beifong manages your trusted articles and social media platform sources. It generates podcasts from the content you trust and curate. It handles the complete pipeline, from data collection and analysis to the production of scripts and visuals.

▶️ [Watch demo video HD](https://www.canva.com/design/DAGoUfv8ICM/Oj-vJ19AvZYDa2SwJrCWKw/watch?utm_content=D[…]hare&utm_medium=link2&utm_source=uniquelinks&utlId=h2508379667)

▶️ [Watch the demo on YouTube](https://youtu.be/dB8FZY3x9EY)

🔗 [Blog](https://arun477.github.io/posts/beifong_podcast_generator/)

## Table of Contents

- [Getting Started](#getting-started)
  - [System Requirements](#system-requirements)
  - [Initial Setup and Installation](#initial-setup-and-installation)
  - [Environment Configuration](#environment-configuration)
  - [Starting the Application](#starting-the-application)
- [How to Use Beifong](#how-to-use-beifong)
  - [Three Usage Methods](#three-usage-methods)
- [Content Processing System](#content-processing-system)
  - [Built-in Content Processors](#built-in-content-processors)
  - [Creating Custom Content Processors](#creating-custom-content-processors)
- [AI Agent and Tools](#ai-agent-and-tools)
  - [Agent Architecture Overview](#agent-architecture-overview)
  - [Adding Custom Tools](#adding-custom-tools)
  - [Configuring Agent Behavior](#configuring-agent-behavior)
- [Web Search and Browser Automation](#web-search-and-browser-automation)
  - [Search Commands](#search-commands)
  - [Social Media Login Sessions](#social-media-login-sessions)
  - [Advanced Persistent Session Configuration](#advanced-persistent-session-configuration)
- [Social Media Monitoring](#social-media-monitoring)
  - [Supported Platforms](#supported-platforms)
  - [Setting Up Scheduled Feed Collection](#setting-up-scheduled-feed-collection)
  - [Viewing AI Insights](#viewing-ai-insights)
  - [Configuring Custom Feeds](#configuring-custom-feeds)
  - [Adding New Social Media Accounts](#adding-new-social-media-accounts)
  - [Scheduling Best Practices](#scheduling-best-practices)
- [Audio and Voice Generation](#audio-and-voice-generation)
  - [Supported TTS Engines](#supported-tts-engines)
  - [Adding New Voice Engines](#adding-new-voice-engines)
- [Integrations](#integrations)
  - [Slack Integration](#slack-integration)
  - [Setting Up Slack App](#setting-up-slack-app)
  - [Required Slack Permissions](#required-slack-permissions)
  - [Environment Configuration](#environment-configuration-1)
  - [Running Slack Integration](#running-slack-integration)
- [Data Storage and File Management](#data-storage-and-file-management)
  - [Database Storage](#database-storage)
  - [Media Asset Storage](#media-asset-storage)
  - [Managing Storage Growth](#managing-storage-growth)
- [Deployment and Access Options](#deployment-and-access-options)
  - [Local Network Access](#local-network-access)
  - [Remote Access Solutions](#remote-access-solutions)
  - [Security](#security)
- [Cloud Options](#cloud-options)
  - [Beifong Cloud Features](#beifong-cloud-features)
- [Troubleshooting](#troubleshooting)
  - [Kokoro Library Installation Issues](#kokoro-library-installation-issues)
  - [Browseruse Installation Issues](#browseruse-installation-issues)
  - [FAISS Library Installation Issues](#faiss-library-installation-issues)
  - [Browser-Based Data Collection Issues](#browser-based-data-collection-issues)
- [Updates](#updates)

## Getting Started

### System Requirements

Before installing Beifong, ensure you have:

- Python 3.11+
- Redis Server
- OpenAI API key
- (Optional) ElevenLabs API key

### Initial Setup and Installation

```bash
# Clone the repository
git clone https://github.com/arun477/beifong.git
cd beifong

# Create virtual environment
cd beifong
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install browser
python -m playwright install

# (Optional but recommended) Download demo content
# Navigate to the beifong directory if not already there
cd beifong  # Skip if already in the beifong folder
# This populates the system with sample data, curated source feeds, and assets
python bootstrap_demo.py
```

### Environment Configuration

Create a `.env` file in the `/beifong` directory with your API keys:

```
OPENAI_API_KEY=your_openai_api_key
ELEVENSLAB_API_KEY=your_elevenlabs_api_key  # Optional
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Starting the Application

Launch all required services in separate terminals (but make sure you start python main.py first before starting others, because the first time run will do db initialization):

⚠️ Make sure to activate the virtual environment in all terminals before starting each script.

```bash
source venv/bin/activate
```

```bash
# Terminal 1: Start the main backend (first time run may take 2 to 3 minutes due to the setup process)
cd beifong
python main.py

# Terminal 2: Start the scheduler
cd beifong
python -m scheduler

# Terminal 3: Start the chat workers
cd beifong
python -m celery_worker

# Verify Redis is running
redis-cli ping
```

#### Optional: Frontend Development Mode

```bash
# Navigate to web directory
cd web

# Install dependencies
npm install

# Start development server
npm start
```

## How to Use Beifong

### Three Usage Methods

Beifong offers flexibility in how you interact with the system:

1. **Interactive Web UI** - Web interface for content management and podcast generation
2. **API Integration** - Programmatic access for custom applications and workflows
3. **Automated Scheduling** - Set up recurring tasks for hands off content processing

## Content Processing System

### Built-in Content Processors

Beifong includes several specialized processors for different content sources:

- **RSS Feed Processor** - Monitors RSS feeds for new articles and content
- **URL Content Processor** - Extracts and processes content from web pages
- **AI Content Analyzer** - Categorizes, summarizes, and analyzes content quality
- **Vector Embedding Processor** - Creates searchable vector representations of content
- **FAISS Search Indexer** - Builds search indices for content discovery
- **Podcast Script Generator** - Creates complete podcast episodes from curated content
- **X.com Social Processor** - Crawls and processes your X.com social media feed
- **Facebook Social Processor** - Crawls and processes your Facebook social media feed

### Creating Custom Content Processors

Extend Beifong's capabilities by adding your own content processors:

#### Step 1: Create Your Processor Module

```python
# processors/my_custom_processor.py
def process_custom_task(parameter1=None, parameter2=None):
    # Your processing logic here
    stats = {"processed": 0, "success": 0, "errors": 0}
    # Processing implementation
    return stats

if __name__ == "__main__":
    stats = process_custom_task()
    print(f"Processed: {stats['processed']}, Success: {stats['success']}")
```

#### Step 2: Register Your Processor

Add your processor to the system in `models/tasks_schemas.py`:

```python
class TaskType(str, Enum):
    # Existing task types...
    my_custom_processor = "my_custom_processor"

TASK_TYPES = {
    # Existing types...
    "my_custom_processor": {
        "name": "My Custom Processor",
        "command": "python -m processors.my_custom_processor",
        "description": "Performs custom processing task",
    },
}
```

#### Step 3: Deploy Your Processor

Create a new task using the API or UI with your custom processor type.

## AI Agent and Tools

### Agent Architecture Overview

Beifong's AI system is built on the [agno](https://github.com/agno-agi/agno) framework and includes:

- **Search Tools** - Semantic search, keyword search, and browser-based web research
- **Content Generation Tools** - Automated script writing, banner creation, and audio production
- **Persistent Session State** - Maintains conversation context across interactions
- **Tool Orchestration** - Manages multi step workflows automatically

### Adding Custom Tools

Extend the agent's capabilities with custom tools:

```python
# tools/my_custom_tool.py
from agno.agent import Agent

def my_custom_tool(agent: Agent, param1: str, param2: str) -> str:
    """Tool description here"""
    agent.session_state["my_key"] = "my_value"
    # Tool implementation
    result = f"Processed {param1} and {param2}"
    return result
```

Register your tool in `services/celery_tasks.py`:

```python
# Add import
from tools.my_custom_tool import my_custom_tool
# Add to tools list
tools = [my_custom_tool]
```

### Configuring Agent Behavior

Modify the agent's instructions and behavior in `db/agent_config_v2.py`:

```python
# Update the instructions to modify the agent's behavior
# Be careful to preserve the core flow stages while adding your customizations
```

## Web Search and Browser Automation

Beifong's search agent has full browser automation capabilities through the [browseruse](https://browser-use.com/) library, enabling web research and automated data collection from any website.

### Search Commands

You can give the agent specific search instructions like:
- *"Go to my X.com and collect top positive and informative feeds"*
- *"Browse Reddit for discussions about AI developments this week"*
- *"Search LinkedIn for recent posts about data science trends"*
- *"Visit news sites and gather articles about renewable energy"*

The agent will navigate websites, interact with page elements, and extract the requested information automatically.

### Social Media Login Sessions

For websites requiring authentication (X.com, Facebook, LinkedIn, etc.), you need to establish logged in sessions:

**Setting Up Social Media Sessions:**

1. **Navigate to Social Tab** in the Beifong web interface
2. **Click "Setup Session"** under the Setup section
3. **Login Process** - A browser window will open where you:
   - Log into your social media accounts normally
   - Complete any verification steps
   - Close the browser when finished
4. **Session Persistence** - Beifong will use these authenticated sessions for future automated searches

### Advanced Persistent Session Configuration

For persistent logged in sessions and advanced browser management:

**Persistent Session Path Configuration:**
- Default browser sessions are stored in `browsers/playwright_persistent_profile_web` folder
- For persistent session paths, modify `tools/web_search` to use `get_browser_session_path()` from `db/config.py`

**Important Persistent Session Management Notes:**
- **Avoid Concurrent Usage** - Ensure no other processes use the same browser session simultaneously
- **Social Monitor Processors** typically use the path from `get_browser_session_path()` function
- **Disable Conflicting Processes** - Switch off social monitoring in the Voyager section if using persistent session paths
- **Future Separation** - Session management will be separated into individual sessions in upcoming updates

**Persistent Session Troubleshooting:**
- If login sessions expire, repeat the Social Tab setup process
- Clear browser data if experiencing authentication issues
- Ensure only one process accesses browser sessions at a time

## Social Media Monitoring

### Supported Platforms

Beifong currently supports automated monitoring for:

- **X.com (Twitter)** - Collects and analyzes your social media feeds
- **Facebook.com** - Monitors your Facebook timeline and interactions

### Setting Up Scheduled Feed Collection

To automatically collect your social media feeds:

1. **Navigate to the Voyager Tab** in the Beifong web interface
2. **Create a Scheduled Task** for social media monitoring
3. **Configure Collection Frequency** - Set how often you want feeds collected
4. **Select Platform** - Choose between X.com or Facebook.com processors

### Viewing AI Insights

Once your social media feeds are collected:

1. **Navigate to the Social Tab** in the web interface
2. **View Comprehensive Analysis** - Each post is analyzed through AI providing:
   - Content sentiment analysis
   - Topic categorization
   - Engagement insights
   - Relevance scoring
3. **Browse Full Insights** - Detailed analytics for all collected social media content

### Configuring Custom Feeds

You can easily customize which feeds to monitor:

**Modifying Feed Sources:**
- Navigate to `/tools/social/` directory
- Update the URLs in the social media processors
- **Monitor Specific Profiles** - Configure to track particular X.com profiles or Facebook pages
- **Custom Feed Types** - Adapt URLs for different types of content feeds

**URL Configuration Examples:**
- Track specific X.com user: Modify URLs to target particular profiles
- Monitor Facebook pages: Configure URLs for specific Facebook feeds
- Custom hashtag monitoring: Set URLs to track specific hashtags or topics

### Adding New Social Media Accounts

Beifong supports easy expansion to additional platforms:

**Currently Supported:**
- X.com (Twitter)
- Facebook.com

**Easy Integration Options:**
- **LinkedIn**
- **Reddit** 
- **Other Platforms** - Most social media platforms can be integrated using the same framework, but you must write a custom scraper or use an API for it.

**Future Updates:**
- Next version will include more built-in connectors for popular social media platforms
- Support for multiple account management per platform

### Scheduling Best Practices

**Important Scheduling Considerations:**

⚠️ **Avoid Concurrent Execution** - When scheduling multiple social media feed collection tasks, ensure they don't run simultaneously. All social media processors share the same persistent browser session.

**Recommended Scheduling Approach:**
- **Stagger Collection Times** - Schedule X.com and Facebook.com collection at different times
- **Allow Processing Gaps** - Leave sufficient time between different social media tasks
- **Monitor Execution Times** - Track how long each collection takes to avoid overlaps

**Example Safe Scheduling:**
- X.com feed collection: Every 2 hours at :00 minutes
- Facebook.com feed collection: Every 2 hours at :30 minutes

**Future Improvements:**
- Next version will provide separate persistent browser sessions for each social media account
- This will eliminate the need for careful scheduling and allow concurrent collection from multiple platforms

## Audio and Voice Generation

### Supported TTS Engines

Beifong supports multiple text to speech options:

**Commercial Options:**
- **OpenAI TTS** 
- **ElevenLabs** 

**Open Source Options:**
- **Kokoro**

### Adding New Voice Engines

The TTS system supports integration of additional engines:

**Potential Next Open Source Integration Options:**
- **[Dia TTS](https://yummy-fir-7a4.notion.site/dia)** 
- **[CSM](https://github.com/SesameAILabs/csm)** 
- **[Orpheus-TTS](https://github.com/canopyai/Orpheus-TTS)** 

Add custom TTS engines through the tts_selector engine interface in the **utils** directory.

## Integrations

Beifong can be integrated with other platforms.

### Slack Integration

Beifong's Slack integration enables you to interact with the AI agent directly from your Slack workspace. Each conversation with Beifong creates a dedicated Slack thread for the session.

**Key Feature:**
- Direct messaging with BeifongAI in Slack channels

### Setting Up Slack App

To integrate Beifong with your Slack workspace, you need to create a Slack app in Socket Mode:

#### Step 1: Create Slack App

1. Visit [Slack API Apps](https://api.slack.com/apps) and click "Create New App"
2. Choose "From scratch" and provide:
   - **App Name**: BeifongAI (or your preferred name)
   - **Workspace**: Select your target Slack workspace
3. **Enable Socket Mode**:
   - Navigate to "Socket Mode" in the left sidebar
   - Toggle "Enable Socket Mode" to ON
   - Generate an App-Level Token with `connections:write` scope
   - Save the **App-Level Token** (this is your `SLACK_APP_TOKEN`)

#### Step 2: Configure Bot User

1. Navigate to "OAuth & Permissions" in the left sidebar
2. Scroll to "Bot Token Scopes" and add the required permissions (see next section)
3. Click "Install to Workspace" and authorize the app
4. Copy the **Bot User OAuth Token** (this is your `SLACK_BOT_TOKEN`)

#### Step 3: Enable Event Subscriptions

1. Navigate to "Event Subscriptions" in the left sidebar
2. Toggle "Enable Events" to ON
3. Add the required bot events (see permissions section below)

### Required Slack Permissions

Your Slack app requires specific permissions to function properly with Beifong:

#### OAuth & Permissions - Bot Token Scopes

Add the following scopes under "OAuth & Permissions" → "Bot Token Scopes":

- **`app_mentions:read`** - View messages that directly mention @BeifongAI in conversations that the app is in
- **`assistant:write`** - Allow BeifongAI to act as an App Agent
- **`channels:history`** - View messages and other content in public channels that BeifongAI has been added to
- **`channels:read`** - View basic information about public channels in a workspace
- **`chat:write`** - Send messages as @BeifongAI
- **`files:read`** - View files shared in channels and conversations that BeifongAI has been added to
- **`files:write`** - Upload, edit, and delete files as @BeifongAI
- **`im:read`** - View basic information about direct messages that BeifongAI has been added to
- **`im:write`** - Start direct messages with people

#### Event Subscriptions - Bot Events

Under "Event Subscriptions" → "Subscribe to bot events", add:

- **`app_mention`** - Subscribe to only the message events that mention your app or bot
  - *Required Scope: `app_mentions:read`*
- **`message.channels`** - A message was posted to a channel
  - *Required Scope: `channels:history`*

### Environment Configuration

Add your Slack tokens to the `.env` file in the `/beifong` directory:

```env
# Existing environment variables...
OPENAI_API_KEY=your_openai_api_key
ELEVENSLAB_API_KEY=your_elevenlabs_api_key  # Optional

# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-bot-user-oauth-token
SLACK_APP_TOKEN=xapp-your-app-level-token

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Running Slack Integration

Once you've configured your Slack app and environment variables:

#### Step 1: Install App in Workspace

1. Ensure your Slack app is installed in your workspace
2. Add BeifongAI to the channels where you want to use it
3. You can also send direct messages to BeifongAI

#### Step 2: Start Slack Integration

```bash
# Navigate to beifong directory
cd beifong

# Ensure your environment is activated
source venv/bin/activate

# Run the Slack integration script
python -m integrations.slack.chat
```

#### Step 3: Interact with BeifongAI

**In Slack Channels:**
- Mention @BeifongAI to start a conversation
- Each mention creates a new thread for context continuity
- Example: `@BeifongAI Can you help me analyze the latest news about AI developments?`

**Reference Documentation:**
- [Slack Socket Mode API](https://api.slack.com/apis/socket-mode)

## Data Storage and File Management

### Database Storage

All application databases are organized in the **databases** directory for easy management and backup.

### Media Asset Storage

Generated podcasts, audio files, and visual assets are stored in the **podcasts** directory.

### Managing Storage Growth

If asset storage grows, consider these storage optimization strategies:

**Cloud Storage Integration:**
- Use s3fs to mount an S3 bucket as a local folder for media assets
- Configure custom storage paths in `.env` to use larger drives

**Automated Cleanup:**
- Set up periodic archiving of older podcast episodes
- Implement automated cleanup for temporary recordings and unused assets
- Configure retention policies for different types of content

**Storage Monitoring:**
- Monitor disk usage as your content library grows
- Set up alerts for storage capacity thresholds

**Note:** More efficient storage management and cloud connectors will be added in the next version.

## Deployment and Access Options

### Local Network Access

```bash
# Start the backend with network access
cd beifong
python main.py --host 0.0.0.0 --port 7000
```

This makes the application accessible via your machine's IP address on your local network.

### Remote Access Solutions

For accessing Beifong from outside your local network (workaround):

#### SSH Port Forwarding
```bash
# Forward local port to remote machine
ssh -L 7000:localhost:7000 username@your-server-ip
```

#### Ngrok Tunneling
```bash
# Create temporary public tunnel
ngrok http 7000
```
Provides a temporary public URL that forwards to your local instance.

### Security

Beifong doesn't include an authentication layer yet. Authentication will be added in the next version.

## Cloud Options

### Beifong Cloud Features
Coming Soon!

✅ Cloud version of Beifong

✅ More social media connectors

✅ More API options. Claude, Gemini, OpenAI, Ollama

✅ Podcast customization with more styles

✅ More voice options

✅ Better data collection and storage management

✅ Authentication layer

## Troubleshooting

### Kokoro Library Installation Issues

If your installation fails due to the Kokoro library, you can skip installing this library and only install it when needed as a TTS engine. Kokoro is optional and only required if you want to use it for text-to-speech generation.

For more information about Kokoro, check the reference: https://github.com/hexgrad/kokoro

### Browseruse Installation Issues

If your installation fails due to browseruse, make sure the Playwright version is properly installed. Browser automation features depend on Playwright being correctly set up.

For more reference and troubleshooting: https://github.com/browser-use/browser-use

### FAISS Library Installation Issues

If the FAISS library installation fails, you can safely ignore this error and skip installing FAISS. This library is only required if you want to use the semantic search feature. If you don't need semantic search functionality, you can safely ignore the FAISS installation failure.

For reference: https://github.com/facebookresearch/faiss

### Browser-Based Data Collection Issues

Some of the data collection features rely on browser automation, which sometimes won't work properly in server environments. While Beifong will still function, some browser dependent features may not work in server environments without proper browser setup.

## Updates

🚀 **[Repo](https://github.com/arun477/beifong)**
