import json
import logging
from typing import Dict, Any, List
from backend.llm.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class StructureAnalyzer:
    """Agent that analyzes data structure and schema"""
    
    def __init__(self, llm_provider: LLMProvider, prompt_template: str):
        self.llm = llm_provider
        self.prompt_template = prompt_template
    
    def analyze(self, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze data structure from sample.
        
        Args:
            sample_data: List of sample review dictionaries
            
        Returns:
            Dict with schema information
        """
        try:
            prompt = f"""
{self.prompt_template}

Sample data (first 3 reviews):
{json.dumps(sample_data[:3], indent=2)}
            """
            
            result = self.llm.generate_json(prompt)
            logger.info("Structure analysis completed")
            print(result)
            return result
        except Exception as e:
            logger.error(f"Error in structure analysis: {str(e)}")
            raise
