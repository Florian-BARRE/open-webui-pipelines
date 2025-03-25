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
from logging import getLogger
from typing import List, Union, Generator, Iterator
from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

# Set up logging
logger = getLogger(__name__)
logger.setLevel("DEBUG")


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

    async def on_startup(self):
        os.environ["OPENAI_API_KEY"] = self.valves.OPENAI_API_KEY
        os.environ["OPENAI_API_BASE"] = self.valves.OPENAI_API_BASE
        os.environ["OPENAI_MODEL_NAME"] = self.valves.OPENAI_MODEL_NAME

        # Create agents
        researcher_agent = Agent(
            role="Researcher",
            goal="Rechercher les dernières informations et tendances sur {topic}",
            verbose=True,
            memory=True,
            backstory="Vous êtes un chercheur spécialisé en technologie et intelligence artificielle.",
            allow_delegation=False
        )

        # Création de l'agent rédacteur
        magazine_writer = Agent(
            role="Magazine Writer",
            goal="Rédiger un article captivant sur le thème {topic}",
            verbose=True,
            memory=True,
            backstory="En tant que rédacteur, vous créez des articles engageants et informatifs.",
            allow_delegation=False
        )

        # Création de l'agent éditeur
        editor_agent = Agent(
            role="Editor",
            goal="Revoir et améliorer l'article sur {topic}",
            verbose=True,
            memory=True,
            backstory="En tant qu'éditeur, vous assurez la qualité et la clarté de l'article.",
            allow_delegation=False
        )

        # Création de l'agent critique
        critic_agent = Agent(
            role="Critic",
            goal="Valider ou rejeter l'article sur {topic}. Si rejeté, fournir des points d'amélioration.",
            verbose=True,
            memory=True,
            backstory="En tant que critique, vous évaluez la qualité de l'article et suggérez des améliorations.",
            allow_delegation=False
        )

        # Création de l'agent manager personnalisé
        manager_agent = Agent(
            role="Manager",
            goal="Gérer et coordonner les tâches entre les agents jusqu'à la validation de l'article.",
            verbose=True,
            memory=True,
            backstory="En tant que manager, vous supervisez le processus de création de l'article.",
            allow_delegation=True
        )

        # Création de la tâche de recherche
        research_task = Task(
            description="Recherchez des informations sur {topic}, y compris les dernières tendances et innovations.",
            expected_output="Un résumé détaillé des tendances récentes et des informations clés sur {topic}.",
            agent=researcher_agent,
            async_execution=False,
        )

        # Création de la tâche de rédaction
        write_article_task = Task(
            description="Rédiger un article de type magazine sur {topic} en vous basant sur la recherche réalisée.",
            expected_output="Un article de 3 à 4 paragraphes sur {topic}, formaté en markdown.",
            agent=magazine_writer,
            async_execution=False,
            output_file="article-magazine.md"
        )

        # Création de la tâche de relecture
        edit_article_task = Task(
            description="Relisez l'article de {topic} et proposez des améliorations pour la fluidité et la clarté.",
            expected_output="Un article amélioré, prêt à être publié.",
            agent=editor_agent,
            async_execution=False,
            output_file="article-magazine-edited.md"
        )

        # Création de la tâche critique
        critique_article_task = Task(
            description="Lisez l'article sur {topic} et déterminez s'il est prêt pour publication. Si non, fournissez des retours.",
            expected_output="Feedback détaillé sur l'article et points d'amélioration.",
            agent=critic_agent,
            async_execution=False,
        )

        # Création du crew avec l'agent manager personnalisé
        self.crew = Crew(
            agents=[researcher_agent, magazine_writer, editor_agent, critic_agent],
            tasks=[research_task, write_article_task, edit_article_task, critique_article_task],
            manager_agent=manager_agent,
            process=Process.hierarchical,  # Utilisation du processus hiérarchique pour une gestion structurée
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

        if body.get("title", False):
            logger.debug("Title Generation Request")
            return "(title generation disabled)"

        logger.debug("User Message: %s", user_message)
        # Execute the pipeline with the user's topic
        self.result = self.crew.kickoff(inputs={'topic': user_message})
        logger.debug("Pipeline completed.")
        logger.debug("Result: %s", self.result)
        # Return the final article after editing and critique
        return self.result
