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

    async def run(self, query: str, interest: str, duration: str) -> None:
        trace_id = gen_trace_id()
        with trace("Tour Research trace", trace_id=trace_id):
            self.printer.update_item(
                "trace_id",
                f"View trace: https://platform.openai.com/traces/{trace_id}",
                is_done=True,
                hide_checkmark=True,
            )
            self.printer.update_item("start", "Starting tour research...", is_done=True)
            planner = await self._get_plan(query, interest, duration)
            print(planner)
            architecture_research = await self._get_architecture(query, interest, planner.architecture)
            historical_research = await self._get_history(query, interest, planner.history)
            culinary_research = await self._get_culinary(query, interest, planner.culinary)
            culture_research = await self._get_culture(query, interest, planner.culture)
            final_tour = await self._get_final_tour(query, interest, duration, architecture_research.output, planner.architecture, historical_research.output, planner.history, culinary_research.output, planner.culinary, culture_research.output, planner.culture)
            
            self.printer.update_item("final_report", "", is_done=True)

            self.printer.end()

        tour_intro = final_tour.introduction
        architecture = final_tour.architecture
        history = final_tour.history
        culinary = final_tour.culinary
        culture = final_tour.culture
        conclusion = final_tour.conclusion

        final = (
            "INTRODUCTION\n\n"
            + tour_intro + "\n\n"

            + "ARCHITECTURE\n\n"
            + architecture + "\n\n"

            + "HISTORY\n\n"
            + history + "\n\n"

            + "CULTURE\n\n"
            + culture + "\n\n"

            + "CULINARY\n\n"
            + culinary + "\n\n"

            + "CONCLUSION\n\n"
            + conclusion
        )
        return final
        
    async def _get_plan(self, query: str, interest: str, duration: str) -> Planner:
        self.printer.update_item("Planner", "Getting Time allocation for each section")
        result = await Runner.run(planner_agent, f"Query: {query} Interest: {interest} Duration: {duration}")
        self.printer.update_item(
            "Planner",
            f"Completed planning",
            is_done=True,
        )
        return result.final_output_as(Planner)
    
    async def _get_history(self, query: str, interest: str, duration: float) -> History:
        self.printer.update_item("History", "Getting Historical Data for Location")
        word_limit = int(duration) * 120 
        result = await Runner.run(historical_agent, f"Query: {query} Interest: {interest} Word Limit: {word_limit} - {word_limit + 20}")
        self.printer.update_item(
            "History",
            f"Completed history research",
            is_done=True,
        )
        return result.final_output_as(History)
        # return result.final_output_as(FinancialSearchPlan)

    async def _get_architecture(self, query: str, interest: str, duration: float):
        self.printer.update_item("Architecture", "Getting Architectural Data for Location")
        word_limit = int(duration) * 120 
        result = await Runner.run(architecture_agent, f"Query: {query} Interest: {interest} Word Limit: {word_limit} - {word_limit + 20}")
        self.printer.update_item(
            "Architecture",
            f"Completed architecture research",
            is_done=True,
        )
        return result.final_output_as(Architecture)
    
    async def _get_culinary(self, query: str, interest: str, duration: float):
        self.printer.update_item("Culinary", "Getting Culinary Data for Location")
        word_limit = int(duration) * 120 
        result = await Runner.run(culinary_agent, f"Query: {query} Interest: {interest} Word Limit: {word_limit} - {word_limit + 20}")
        self.printer.update_item(
            "Culinary",
            f"Completed culinary research",
            is_done=True,
        )
        return result.final_output_as(Culinary)
    
    async def _get_culture(self, query: str, interest: str, duration: float):
        self.printer.update_item("Culture", "Getting Cultural Data for Location")
        word_limit = int(duration) * 120 
        result = await Runner.run(culture_agent, f"Query: {query} Interest: {interest} Word Limit: {word_limit} - {word_limit + 20}")
        self.printer.update_item(
            "Culture",
            f"Completed culture research",
            is_done=True,
        )
        return result.final_output_as(Culture)
    
    async def _get_final_tour(self, query: str, interest: str, duration: float, architecture: str, architecture_dur: float, history: str, history_dur: float, culinary: str, culinary_dur: float, culture: str, culture_dur:float):
        self.printer.update_item("Final Tour", "Getting Final Tour")
        result = await Runner.run(
                    orchestrator_agent,
                    f"""Query: {query}
                Interest: {interest}
                Total Tour Duration (in minutes): {duration}

                Word Limit Allocation:
                - Architecture: {architecture_dur*100}
                - History: {history_dur*100}
                - Culture: {culture_dur*100}
                - Culinary: {culinary_dur*100}

                Content Sections:
                Architecture:
                {architecture}

                History:
                {history}

                Culture:
                {culture}

                Culinary:
                {culinary}
                """
                )
        self.printer.update_item(
            "Final Tour",
            f"Completed Final Tour Guide Creation",
            is_done=True,
        )
        return result.final_output_as(FinalTour)