from crewai_tools import BaseTool
from typing import Dict, List, Union, Optional
from openai import OpenAI
import os
from pydantic import Field, BaseModel
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InputValidationError(Exception):
    """Custom exception for input validation errors"""
    pass

class APIError(Exception):
    """Custom exception for API-related errors"""
    pass

class TrendAnalyzerTool(BaseTool):
    name: str = "Trend Analyzer"
    description: str = "Analyzes trends across multiple news article summaries and suggests potential outcomes and business ideas."
    api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""), description="API key for OpenAI")

    def validate_input(self, data: Dict) -> None:
        """
        Validates the input data structure.
        
        Args:
            data: Dictionary containing the input data
            
        Raises:
            InputValidationError: If the input data is invalid
        """
        if not isinstance(data, dict):
            raise InputValidationError("Input must be a dictionary")
        
        if "key_points" not in data and "summary" not in data:
            raise InputValidationError("Input must contain either 'key_points' or 'summary'")
            
        if "key_points" in data and not isinstance(data["key_points"], list):
            raise InputValidationError("key_points must be a list")

    def _run(self, input_data: Union[str, Dict]) -> Dict[str, list]:
        """
        Analyze summaries to identify trends and suggest outcomes and business ideas.
        
        Args:
            input_data: A dictionary containing structured news summaries
        Returns:
            Dict[str, list]: A dictionary with trends, outcomes, and business ideas
        """
        try:
            # Parse input data
            logger.info("Parsing input data")
            if isinstance(input_data, str):
                try:
                    data = json.loads(input_data)
                    if "input_data" in data:
                        data = data["input_data"]
                except json.JSONDecodeError as e:
                    raise InputValidationError(f"Failed to parse JSON input: {str(e)}")
            else:
                data = input_data

            # Validate input
            self.validate_input(data)

            # Extract summaries and key points
            summary_text = ""
            if "key_points" in data:
                summary_text = "\n\n".join(data["key_points"])
            elif "summary" in data:
                summary_text = data["summary"]
            
            logger.info(f"Extracted summary text: {summary_text[:100]}...")

            # Verify API key
            if not self.api_key:
                self.api_key = os.getenv("OPENAI_API_KEY")
                if not self.api_key:
                    raise APIError("OpenAI API key not found in environment variables")

            client = OpenAI(api_key=self.api_key)
            
            prompt = self._create_prompt(summary_text)
            
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an expert analyst specializing in identifying trends, implications, and business opportunities from news data."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.7
                )
            except Exception as e:
                raise APIError(f"OpenAI API call failed: {str(e)}")

            analysis = response.choices[0].message.content.strip()
            logger.info("Successfully received analysis from OpenAI")

            return self._parse_analysis(analysis)

        except InputValidationError as e:
            logger.error(f"Input validation error: {str(e)}")
            return self._error_response(f"Input validation error: {str(e)}")
        except APIError as e:
            logger.error(f"API error: {str(e)}")
            return self._error_response(f"API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return self._error_response(f"Unexpected error: {str(e)}")

    def _create_prompt(self, summary_text: str) -> str:
        """Creates the analysis prompt"""
        return (
            "Based on these news summaries:\n\n"
            f"{summary_text}\n\n"
            "Please analyze and identify:\n"
            "1. Key emerging trends\n"
            "2. Potential future implications and outcomes\n"
            "3. Business opportunities arising from these developments\n\n"
            "Format your response exactly as follows (provide at least 3 of each):\n"
            "Trend: [specific trend description]\n"
            "Trend: [specific trend description]\n"
            "Trend: [specific trend description]\n"
            "Outcome: [specific outcome description]\n"
            "Outcome: [specific outcome description]\n"
            "Outcome: [specific outcome description]\n"
            "Business Idea: [specific idea description]\n"
            "Business Idea: [specific idea description]\n"
            "Business Idea: [specific idea description]"
        )

    def _parse_analysis(self, analysis: str) -> Dict[str, list]:
        """Parses the analysis response"""
        trends = [line.strip() for line in analysis.split('\n') if line.strip().startswith('Trend:')]
        outcomes = [line.strip() for line in analysis.split('\n') if line.strip().startswith('Outcome:')]
        business_ideas = [line.strip() for line in analysis.split('\n') if line.strip().startswith('Business Idea:')]

        return {
            "trends": trends or ["No clear trends identified"],
            "outcomes": outcomes or ["No specific outcomes predicted"],
            "business_ideas": business_ideas or ["No business ideas generated"]
        }

    def _error_response(self, error_message: str) -> Dict[str, list]:
        """Creates a standardized error response"""
        return {
            "trends": [f"Error analyzing trends: {error_message}"],
            "outcomes": ["Analysis failed"],
            "business_ideas": ["Analysis failed"]
        }

    async def _arun(self, input_data: Union[str, Dict]) -> Dict[str, list]:
        """Async version of the run method"""
        return self._run(input_data)
