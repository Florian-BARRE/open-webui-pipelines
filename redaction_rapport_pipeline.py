"""
title: CrewAI Redaction Rapport Pipeline
author: Florian Barre
author_url: https://github.com/Florian-BARRE
git_url: https://github.com/Florian-BARRE/open-webui-pipelines
description: A CrewAI pipeline for researching, writing, editing, and critiquing articles.
required_open_webui_version: 0.4.3
version: 0.1.0
license: GPL-3.0
"""

import os
import logging
from typing import List, Union, Generator, Iterator
from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Pipeline:
    class Valves(BaseModel):
        OPENAI_API_KEY: str = Field(default="813", description="OpenAI API key")
        OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1", description="OpenAI provider URL")
        OPENAI_MODEL_NAME: str = Field(default="gpt-3.5-turbo", description="LLM Model")

    def __init__(self):
        from crewai.telemetry import Telemetry

        def noop(*args, **kwargs):
            pass

        def disable_crewai_telemetry():
            for attr in dir(Telemetry):
                if callable(getattr(Telemetry, attr)) and not attr.startswith("__"):
                    setattr(Telemetry, attr, noop)

        disable_crewai_telemetry()

        self.name = "Redaction Rapport Pipeline"

        # Initialize valve parameters
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )

        logger.debug("Valves: %s", self.valves)

        self.crew = None
        self.result = None

        self.researcher_agent = None
        self.writer_agent = None
        self.editor_agent = None
        self.critic_agent = None

        self.research_task = None
        self.write_task = None
        self.edit_task = None
        self.critique_task = None

    async def on_startup(self):
        os.environ["OPENAI_API_KEY"] = self.valves.OPENAI_API_KEY
        os.environ["OPENAI_API_BASE"] = self.valves.OPENAI_API_BASE
        os.environ["OPENAI_MODEL_NAME"] = self.valves.OPENAI_MODEL_NAME

        # Create agents
        self.researcher_agent = Agent(
            role="Researcher",
            goal="Research information on {topic}",
            verbose=True,
            memory=True,
            backstory="You are a researcher specializing in technology and AI.",
            allow_delegation=False
        )

        self.writer_agent = Agent(
            role="Writer",
            goal="Write an article on {topic}",
            verbose=True,
            memory=True,
            backstory="You are an experienced technical writer.",
            allow_delegation=False
        )

        self.editor_agent = Agent(
            role="Editor",
            goal="Edit the article on {topic}",
            verbose=True,
            memory=True,
            backstory="You are an editor attentive to detail and quality.",
            allow_delegation=False
        )

        self.critic_agent = Agent(
            role="Critic",
            goal="Evaluate and validate the article on {topic}",
            verbose=True,
            memory=True,
            backstory="You are a discerning critic, ensuring excellence.",
            allow_delegation=False
        )

        # Create tasks
        self.research_task = Task(
            description="Research relevant information on {topic}.",
            expected_output="Summary of key information on {topic}.",
            agent=self.researcher_agent,
            async_execution=False
        )

        self.write_task = Task(
            description="Write a comprehensive article on {topic} based on research.",
            expected_output="Article of 3 to 4 paragraphs on {topic}, formatted in markdown.",
            agent=self.writer_agent,
            async_execution=False
        )

        self.edit_task = Task(
            description="Edit the article on {topic} to improve clarity and quality.",
            expected_output="Revised article, ready for validation.",
            agent=self.editor_agent,
            async_execution=False
        )

        self.critique_task = Task(
            description="Evaluate the article on {topic} and provide feedback for validation.",
            expected_output="Detailed comments on the article and suggestions for improvement.",
            agent=self.critic_agent,
            async_execution=False
        )

        # Create the crew with a sequential process
        self.crew = Crew(
            agents=[self.researcher_agent, self.writer_agent, self.editor_agent, self.critic_agent],
            tasks=[self.research_task, self.write_task, self.edit_task, self.critique_task],
            process=Process.sequential
        )

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        pass

    def pipe(
            self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        # Initialize the crew if not already done
        if self.crew is None:
            self.on_startup()

        logger.debug("User Message: %s", user_message)
        # Execute the pipeline with the user's topic
        self.result = self.crew.kickoff(inputs={'topic': user_message})
        logger.debug("Pipeline completed.")
        logger.debug("Result: %s", self.result)
        # Return the final article after editing and critique
        return self.result
