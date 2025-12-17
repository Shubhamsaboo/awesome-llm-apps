# 📧 Email Generation Agent with Structured Output

A tutorial demonstrating how to implement structured output using Google's ADK (Agent Development Kit) framework. This example uses an email generator agent to show how to create type-safe, structured responses with Pydantic schemas and Gemini 3 Flash model.

## Tutorial Features

- 📝 **Structured Output Implementation**: 
  - Learn how to use Pydantic schemas for type-safe output
  - Understand how to define structured response formats
  - See how Google ADK handles structured responses

- 🎯 **Email Generator Example**: 
  - Practical example using email generation as the use case
  - Shows how to create professional email content with proper structure
  - Demonstrates real-world application of structured output

- 🔧 **Google ADK Best Practices**: 
  - Simple agent definition with clear instructions
  - Proper use of output schemas for reliable results
  - Minimal codebase demonstrating core concepts

## 🚀 Getting Started

1. **Set up your environment**:
   ```bash
   cd 3_2_email_agent
   
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
   2. Select the "email_generator_agent"
   3. Enter your email request (e.g. "Write a professional email to schedule a meeting with a client")
   4. The response will be a structured JSON with subject and body fields

## Tutorial Overview

This tutorial demonstrates structured output implementation in Google ADK:

1. **Agent Definition**: Learn how to create a `LlmAgent` with Gemini 3 Flash
2. **Output Schema**: Understand how to use Pydantic models for structured responses
3. **Instructions**: See how to write clear prompts for structured output
4. **Structured Response**: Learn how to handle JSON responses with defined schemas

## Code Structure

- `agent.py`: Contains the main agent definition and Pydantic schema
- `__init__.py`: Module initialization for easy imports

## Dependencies

- `google-adk`: Google's Agent Development Kit
- `pydantic`: Data validation and settings management

## How Structured Output Works

This tutorial shows how Google ADK handles structured output:

1. **Input Processing**: Takes natural language requests and processes them through the agent
2. **Content Generation**: Uses Gemini 3 Flash to generate content based on instructions
3. **Output Structuring**: Automatically formats responses according to the Pydantic schema
4. **Response Validation**: Ensures the output matches the defined structure and types

This approach demonstrates how to create reliable, type-safe responses in Google ADK applications. 