# 🚀 AI Email GTM Reachout Agent

### 🎓 FREE Step-by-Step Tutorial 
**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-an-ai-email-gtm-outreach-agent-team) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

An intelligent, fully automated B2B outreach system that discovers companies, finds decision makers, researches company intelligence, and generates personalized cold emails using AI agents.

## ✨ Features

### 🔍 **Automated Company Discovery**
- Uses Exa search to find target companies based on industry, size, and business criteria
- Identifies companies showing growth, recent funding, or expansion
- Supports multiple company categories: SaaS/Technology, E-commerce/Retail, Financial Services, Healthcare/Biotech, Manufacturing/Industrial

### 👥 **Intelligent Contact Finding**
- Automatically discovers decision makers in target departments
- Finds email addresses and LinkedIn profiles
- Targets roles like CEO, CTO, VP of Engineering, CMO, VP Marketing, Sales Directors, HR Directors

### 🔬 **Deep Company Research**
- Comprehensive company intelligence gathering
- Analyzes website, recent news, product offerings, technology stack
- Identifies pain points, growth opportunities, and market positioning
- Extracts insights relevant for personalized outreach

### ✉️ **Personalized Email Generation**
- Creates highly personalized cold emails based on research
- Uses department-specific templates for different professional types
- Maintains friendly, conversational tone (20-year-old sales rep style)
- Avoids corporate jargon and clichés
- References specific company challenges and achievements

### 🎯 **Smart Targeting**
- **Company Categories**: SaaS/Technology, E-commerce, Financial Services, Healthcare, Manufacturing
- **Company Sizes**: Startup (1-50), SMB (51-500), Enterprise (500+), All Sizes
- **Target Departments**: GTM (Sales & Marketing), HR, Engineering/Tech, Operations, Finance, Product, Executive Leadership
- **Service Types**: Software Solution, Consulting Services, Professional Services, Technology Platform, Custom Development

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd ai_email_gtm_reachout_agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

**Note**: Make sure you have Agno version 2.0.4 or higher installed.

3. **Set up API keys**
```bash
# Required API keys
export EXA_API_KEY="your_exa_api_key"
export OPENAI_API_KEY="your_openai_api_key"
```

## 🚀 Quick Start

1. **Run the application**
```bash
streamlit run ai_email_gtm_reachout.py
```

2. **Configure your outreach campaign**:
   - Select target company category and size
   - Choose departments to target
   - Enter your contact information
   - Describe your service offering
   - Select personalization level

3. **Launch automated campaign**:
   - Click "Start Automated Campaign"
   - Watch as AI discovers companies, finds contacts, researches details, and generates personalized emails

## 📋 Usage Guide

### Step 1: Target Company Discovery
- Choose from predefined company categories
- Select preferred company size
- Specify number of companies to find (1-20)

### Step 2: Your Information
- **Required**: Name, Email, Organization, Service Description
- **Optional**: LinkedIn, Phone, Website, Calendar Link

### Step 3: Outreach Configuration
- Select service/product category
- Choose personalization level (Basic/Medium/Deep)
- Pick target departments

### Step 4: Generate Campaign
- Review your configuration
- Click "Start Automated Campaign"
- Monitor progress and view generated emails

## 🎨 Email Templates

The system includes department-specific templates:

### GTM (Sales & Marketing)
- Software Solution templates
- Consulting Services templates

### Human Resources
- Software Solution templates
- Consulting Services templates
- Investment Opportunity templates

### Marketing Professional
- Product Demo templates
- Service Offering templates

### B2B Sales Representative
- Product Demo templates
- Service Offering templates

## 🔧 Configuration Options

### Company Categories
- **SaaS/Technology Companies**: Software, cloud services, tech platforms
- **E-commerce/Retail**: Online retail, marketplaces, D2C brands
- **Financial Services**: Banks, fintech, insurance, investment firms
- **Healthcare/Biotech**: Healthcare providers, biotech, health tech
- **Manufacturing/Industrial**: Manufacturing, industrial automation, supply chain

### Personalization Levels
- **Basic**: Standard personalization with company name and basic details
- **Medium**: Includes recent company news and achievements
- **Deep**: Comprehensive personalization with specific pain points and opportunities

## 📊 Output Format

Each generated email includes:
- **Personalized Email**: Ready-to-send cold email
- **Company Research**: Detailed company intelligence
- **Contacts Found**: Decision maker information

## 🔑 API Requirements

### Exa API
- Used for company discovery and research
- Get your API key from [exa.ai](https://exa.ai)
- Required for finding companies and gathering intelligence

### OpenAI API
- Used for email generation and content creation
- Get your API key from [platform.openai.com](https://platform.openai.com)
- Required for AI-powered email personalization

## 🎯 Use Cases

### Sales Teams
- Automated prospecting for B2B sales
- Personalized outreach at scale
- Target specific industries and company sizes

### Marketing Agencies
- Client prospecting campaigns
- Lead generation for multiple clients
- Industry-specific outreach strategies

### Consultants
- Business development automation
- Service offering promotion
- Professional network expansion

### Startups
- Investor outreach
- Partnership development
- Customer acquisition
