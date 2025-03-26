from __future__ import annotations

import asyncio
import time
import json
from collections.abc import Sequence

from rich.console import Console

from agents import Runner, RunResult, custom_span, gen_trace_id, trace

from agent import History, historical_agent
from agent import Culinary,culinary_agent
from agent import Culture,culture_agent
from agent import Architecture,architecture_agent
from agent import Planner, planner_agent
from agent import FinalTour, orchestrator_agent
from printer import Printer


class TourManager:
    """
    Orchestrates the full flow
    """

    def __init__(self) -> None:
        self.console = Console()
        self.printer = Printer(self.console)

    async def run(self, query: str, interests: list, duration: str) -> None:
        trace_id = gen_trace_id()
        with trace("Tour Research trace", trace_id=trace_id):
            self.printer.update_item(
                "trace_id",
                "View trace: https://platform.openai.com/traces/{}".format(trace_id),
                is_done=True,
                hide_checkmark=True,
            )
            self.printer.update_item("start", "Starting tour research...", is_done=True)
            
            # Get plan based on selected interests
            planner = await self._get_plan(query, interests, duration)
            
            # Initialize research results
            research_results = {}
            
            # Calculate word limits based on duration
            # Assuming average speaking rate of 150 words per minute
            words_per_minute = 150
            total_words = int(duration) * words_per_minute
            words_per_section = total_words // len(interests)
            
            # Only research selected interests
            if "Architecture" in interests:
                research_results["architecture"] = await self._get_architecture(query, interests, words_per_section)
            
            if "History" in interests:
                research_results["history"] = await self._get_history(query, interests, words_per_section)
            
            if "Culinary" in interests:
                research_results["culinary"] = await self._get_culinary(query, interests, words_per_section)
            
            if "Culture" in interests:
                research_results["culture"] = await self._get_culture(query, interests, words_per_section)
            
            # Get final tour with only selected interests
            final_tour = await self._get_final_tour(
                query, 
                interests, 
                duration, 
                research_results
            )
            
            self.printer.update_item("final_report", "", is_done=True)
            self.printer.end()

        # Build final tour content based on selected interests
        sections = []
        
        # Add selected interest sections without headers
        if "Architecture" in interests:
            sections.append(final_tour.architecture)
        if "History" in interests:
            sections.append(final_tour.history)
        if "Culture" in interests:
            sections.append(final_tour.culture)
        if "Culinary" in interests:
            sections.append(final_tour.culinary)
        
        # Format final tour with natural transitions
        final = ""
        for i, content in enumerate(sections):
            if i > 0:
                final += "\n\n"  # Add spacing between sections
            final += content
            
        return final
        
    async def _get_plan(self, query: str, interests: list, duration: str) -> Planner:
        self.printer.update_item("Planner", "Planning your personalized tour...")
        result = await Runner.run(
            planner_agent, 
            "Query: {} Interests: {} Duration: {}".format(query, ', '.join(interests), duration)
        )
        self.printer.update_item(
            "Planner",
            "Completed planning",
            is_done=True,
        )
        return result.final_output_as(Planner)
    
    async def _get_history(self, query: str, interests: list, word_limit: int) -> History:
        self.printer.update_item("History", "Researching historical highlights...")
        result = await Runner.run(
            historical_agent, 
            "Query: {} Interests: {} Word Limit: {} - {}\n\nInstructions: Create engaging historical content for an audio tour. Focus on interesting stories and personal connections. Make it conversational and include specific details that would be interesting to hear while walking. Include specific locations and landmarks where possible. The content should be approximately {} words when spoken at a natural pace.".format(query, ', '.join(interests), word_limit, word_limit + 20, word_limit)
        )
        self.printer.update_item(
            "History",
            "Completed history research",
            is_done=True,
        )
        return result.final_output_as(History)

    async def _get_architecture(self, query: str, interests: list, word_limit: int):
        self.printer.update_item("Architecture", "Exploring architectural wonders...")
        result = await Runner.run(
            architecture_agent, 
            "Query: {} Interests: {} Word Limit: {} - {}\n\nInstructions: Create engaging architectural content for an audio tour. Focus on visual descriptions and interesting design details. Make it conversational and include specific buildings and their unique features. Describe what visitors should look for and why it matters. The content should be approximately {} words when spoken at a natural pace.".format(query, ', '.join(interests), word_limit, word_limit + 20, word_limit)
        )
        self.printer.update_item(
            "Architecture",
            "Completed architecture research",
            is_done=True,
        )
        return result.final_output_as(Architecture)
    
    async def _get_culinary(self, query: str, interests: list, word_limit: int):
        self.printer.update_item("Culinary", "Discovering local flavors...")
        result = await Runner.run(
            culinary_agent, 
            "Query: {} Interests: {} Word Limit: {} - {}\n\nInstructions: Create engaging culinary content for an audio tour. Focus on local specialties, food history, and interesting stories about restaurants and dishes. Make it conversational and include specific recommendations. Describe the flavors and cultural significance of the food. The content should be approximately {} words when spoken at a natural pace.".format(query, ', '.join(interests), word_limit, word_limit + 20, word_limit)
        )
        self.printer.update_item(
            "Culinary",
            "Completed culinary research",
            is_done=True,
        )
        return result.final_output_as(Culinary)
    
    async def _get_culture(self, query: str, interests: list, word_limit: int):
        self.printer.update_item("Culture", "Exploring cultural highlights...")
        result = await Runner.run(
            culture_agent, 
            "Query: {} Interests: {} Word Limit: {} - {}\n\nInstructions: Create engaging cultural content for an audio tour. Focus on local traditions, arts, and community life. Make it conversational and include specific cultural venues and events. Describe the atmosphere and significance of cultural landmarks. The content should be approximately {} words when spoken at a natural pace.".format(query, ', '.join(interests), word_limit, word_limit + 20, word_limit)
        )
        self.printer.update_item(
            "Culture",
            "Completed culture research",
            is_done=True,
        )
        return result.final_output_as(Culture)
    
    async def _get_final_tour(self, query: str, interests: list, duration: float, research_results: dict):
        self.printer.update_item("Final Tour", "Creating your personalized tour...")
        
        # Build content sections based on selected interests
        content_sections = []
        for interest in interests:
            if interest.lower() in research_results:
                content_sections.append(research_results[interest.lower()].output)
        
        # Calculate total words based on duration
        # Assuming average speaking rate of 150 words per minute
        words_per_minute = 150
        total_words = int(duration) * words_per_minute
        
        # Create the prompt with proper string formatting
        prompt = (
            "Query: {}\n"
            "Selected Interests: {}\n"
            "Total Tour Duration (in minutes): {}\n"
            "Target Word Count: {}\n\n"
            "Content Sections:\n{}\n\n"
            "Instructions: Create a natural, conversational audio tour that focuses only on the selected interests. "
            "Make it feel like a friendly guide walking alongside the visitor, sharing interesting stories and insights. "
            "Use natural transitions between topics and maintain an engaging but relaxed pace. "
            "Include specific locations and landmarks where possible. "
            "Add natural pauses and transitions as if walking between locations. "
            "Use phrases like 'as we walk', 'look to your left', 'notice how', etc. "
            "Make it interactive and engaging, as if the guide is actually there with the visitor. "
            "Start with a warm welcome and end with a natural closing thought. "
            "The total content should be approximately {} words when spoken at a natural pace of 150 words per minute. "
            "This will ensure the tour lasts approximately {} minutes."
        ).format(
            query,
            ', '.join(interests),
            duration,
            total_words,
            '\n\n'.join(content_sections),
            total_words,
            duration
        )
        
        result = await Runner.run(
            orchestrator_agent,
            prompt
        )
        
        self.printer.update_item(
            "Final Tour",
            "Completed Final Tour Guide Creation",
            is_done=True,
        )
        return result.final_output_as(FinalTour)