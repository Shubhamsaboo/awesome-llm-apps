from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI
from agents.news_collector import NewsAPITool
from agents.fact_checker import FactCheckerTool
from agents.summary_writer import SummaryWriterTool
from agents.trend_analyzer import TrendAnalyzerTool
import os

class NewsSummarizerAnalyzerCrew:
    def __init__(self):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.llm = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo")
        self.crew = self.create_crew()

    def create_crew(self) -> Crew:
        return Crew(
            agents=[
                self.news_collector(),
                self.fact_checker(),
                self.summary_writer(),
                self.trend_analyzer()
            ],
            tasks=[
                self.news_collector_task(),
                self.fact_checker_task(),
                self.summary_writer_task(),
                self.trend_analyzer_task()
            ],
            process=Process.sequential,
            verbose=True
        )

    def news_collector(self) -> Agent:
        return Agent(
            name="News Collector",
            role="Collects news articles",
            goal="Gather relevant news articles",
            backstory="An expert in finding and collecting news from various sources",
            tools=[NewsAPITool()],
            verbose=True,
            llm=self.llm
        )

    def fact_checker(self) -> Agent:
        return Agent(
            name="Fact Checker",
            role="Verifies information in news articles",
            goal="Ensure the accuracy of collected news",
            backstory="A meticulous fact-checker with years of experience",
            tools=[FactCheckerTool()],
            verbose=True,
            llm=self.llm,
            custom_prompt="When using the Fact Checker tool, always format the input as a list of dictionaries. Each dictionary should have 'title', 'url', and 'snippet' keys."
        )

    def summary_writer(self) -> Agent:
        return Agent(
            name="Summary Writer",
            role="Summarizes news articles",
            goal="Create concise and informative summaries",
            backstory="A skilled writer with a talent for distilling complex information",
            tools=[SummaryWriterTool()],
            verbose=True,
            llm=self.llm
        )

    def trend_analyzer(self) -> Agent:
        return Agent(
            name="Trend Analyzer",
            role="Analyzes trends in news",
            goal="Identify and report on emerging trends",
            backstory="An expert in data analysis and trend forecasting",
            tools=[TrendAnalyzerTool()],
            verbose=True,
            llm=self.llm
        )

    def news_collector_task(self) -> Task:
        return Task(
            description="Gather the latest relevant news articles on the specified topic: {topic}",
            agent=self.news_collector(),
            expected_output="A list of dictionaries, each containing 'title', 'url', and 'snippet' keys for each relevant news article."
        )

    def fact_checker_task(self) -> Task:
        return Task(
            description="Verify the accuracy of news articles collected on the topic. Use the Fact Checker tool with a list of article dictionaries as input. Each article dictionary should have 'title', 'url', and 'snippet' keys.",
            agent=self.fact_checker(),
            expected_output="A list of strings, where each string is the title of an article that has been verified as factual."
        )

    def summary_writer_task(self) -> Task:
        return Task(
            description="Write concise summaries of the verified news articles. Each article is represented by its title.",
            agent=self.summary_writer(),
            expected_output="""
            A dictionary containing:
            - "title": The title of the summary.
            - "summary": A brief overview of the main findings or conclusions.
            - "key_points": A list of key points or highlights from the summary.
            - "sources": A list of article titles that were summarized.
            """
        )

    def trend_analyzer_task(self) -> Task:
        return Task(
            description="Analyze trends in the summarized news. The input will be a dictionary containing the summary of all topics.",
            agent=self.trend_analyzer(),
            expected_output="An insightful analysis report identifying emerging trends, patterns, and potential future developments based on the summarized news data, including strategic implications and potential business ideas."
        )

    def kickoff(self, topic):
        return self.crew.kickoff(inputs={"topic": topic})
