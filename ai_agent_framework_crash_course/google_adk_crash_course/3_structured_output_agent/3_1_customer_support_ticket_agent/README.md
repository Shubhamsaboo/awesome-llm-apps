# 🎫 Customer Support Ticketing Agent with Structured Output

A tutorial demonstrating how to implement a structured customer support ticketing system using Google's ADK (Agent Development Kit) framework. This example shows how to create type-safe, structured support tickets with priority levels, categories, and resolution estimates using Pydantic schemas and Gemini 3 Flash model.

## Tutorial Features

- 🎫 **Structured Support Tickets**: 
  - Learn how to create comprehensive support ticket schemas
  - Understand priority levels and categorization
  - See how to estimate resolution times

- 🔧 **Advanced Schema Design**: 
  - Complex Pydantic models with enums and optional fields
  - Proper field validation and descriptions
  - Type-safe structured responses

- 🎯 **Real-World Application**: 
  - Practical customer support use case
  - Shows how to handle different types of support requests
  - Demonstrates structured output for business processes

- 📊 **Priority Management**: 
  - Four-tier priority system (Low, Medium, High, Critical)
  - Automatic priority assignment based on issue description
  - Category-based routing for different departments

## 🚀 Getting Started

1. **Set up your environment**:
   ```bash
   cd 3_1_customer_support_ticket_agent
   
   # Copy the environment template
   cp env.example .env
   
   # Edit .env and add your Google AI API key
   # Get your API key from: https://aistudio.google.com/
   ```

2. **Install dependencies**:
   ```bash
   # Navigate back to the directory
   cd ..

   # Install required packages
   pip install -r requirements.txt
   ```

3. **Run the Agent**
   ```bash
   # Start the ADK web interface
   adk web
   ```
   Then:
   1. Open the web interface in your browser
   2. Select the "support_ticket_creator" agent
   3. Enter your support request (e.g., "I can't log into my account and I have an important meeting in 2 hours")
   4. The response will be a structured JSON with all ticket details

## Tutorial Overview

This tutorial demonstrates advanced structured output implementation in Google ADK:

1. **Complex Schema Design**: Learn how to create sophisticated Pydantic models
2. **Enum Usage**: Understand how to use enums for constrained values
3. **Optional Fields**: See how to handle optional data with proper defaults
4. **Business Logic**: Learn how to implement real-world business processes

## Code Structure

- `customer_support_agent/agent.py`: Contains the main agent definition and SupportTicket schema
- `customer_support_agent/__init__.py`: Module initialization for easy imports

## Support Ticket Schema

The agent creates structured tickets with the following fields:

- **title**: Concise summary of the issue
- **description**: Detailed problem description
- **priority**: Priority level (low, medium, high, critical)
- **category**: Department (Technical, Billing, Account, Product)
- **steps_to_reproduce**: Optional list of steps for technical issues
- **estimated_resolution_time**: Estimated time to resolve

## Example Usage

**Input**: "My payment failed and I'm getting charged twice for the same service"

**Output**:
```json
{
  "title": "Duplicate payment charge issue",
  "description": "Customer reports payment failure followed by duplicate charges for the same service",
  "priority": "high",
  "category": "Billing",
  "steps_to_reproduce": null,
  "estimated_resolution_time": "4-6 hours"
}
```

## Dependencies

- `google-adk`: Google's Agent Development Kit
- `pydantic`: Data validation and settings management

## How Structured Output Works

This tutorial shows how Google ADK handles complex structured output:

1. **Input Processing**: Takes natural language support requests
2. **Context Analysis**: Analyzes the issue severity and type
3. **Structured Generation**: Creates comprehensive tickets with all required fields
4. **Validation**: Ensures output matches the defined schema and business rules

This approach demonstrates how to create reliable, business-ready structured responses in Google ADK applications. 