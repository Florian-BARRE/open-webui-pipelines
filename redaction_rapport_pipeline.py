"""
title: Llama Index Pipeline
author: open-webui
date: 2024-05-30
version: 1.0
license: MIT
description: A pipeline for retrieving relevant information from a knowledge base using the Llama Index library.
requirements: llama-index
"""

import os
from typing import List, Union, Generator, Iterator
from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field




class Pipeline:
    class Valves(BaseModel):
        OPENAI_API_KEY: str = Field(default="813", description="OpenAI API key")
        OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1", description="OpenAI provider URL")
        OPENAI_MODEL_NAME: str = Field(default="gpt-3.5-turbo", description="LLM Model")

    def __init__(self):
        from crewai.telemetry import Telemetry

        def noop(*args, **kwargs):
            pass

        def disable_crewai_teleketry():
            for attr in dir(Telemetry):
                if callable(getattr(Telemetry, attr)) and not attr.startswith("__"):
                    setattr(Telemetry, attr, noop)

        disable_crewai_teleketry()

        self.name = "Redaction Rapport Pipeline"

        # Initialize valve paramaters
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )

        print("Valves:", self.valves)

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

        # Création des agents
        self.researcher_agent = Agent(
            role="Researcher",
            goal="Rechercher des informations sur {topic}",
            verbose=True,
            memory=True,
            backstory="Vous êtes un chercheur spécialisé en technologie et IA.",
            allow_delegation=False
        )

        self.writer_agent = Agent(
            role="Writer",
            goal="Rédiger un article sur {topic}",
            verbose=True,
            memory=True,
            backstory="Vous êtes un rédacteur expérimenté en rédaction technique.",
            allow_delegation=False
        )

        self.editor_agent = Agent(
            role="Editor",
            goal="Éditer l'article sur {topic}",
            verbose=True,
            memory=True,
            backstory="Vous êtes un éditeur attentif aux détails et à la qualité.",
            allow_delegation=False
        )

        self.critic_agent = Agent(
            role="Critic",
            goal="Évaluer et valider l'article sur {topic}",
            verbose=True,
            memory=True,
            backstory="Vous êtes un critique exigeant, garant de l'excellence.",
            allow_delegation=False
        )

        # Création des tâches
        self.research_task = Task(
            description="Rechercher des informations pertinentes sur {topic}.",
            expected_output="Résumé des informations clés sur {topic}.",
            agent=self.researcher_agent,
            async_execution=False
        )

        self.write_task = Task(
            description="Rédiger un article complet sur {topic} basé sur la recherche.",
            expected_output="Article de 3 à 4 paragraphes sur {topic}, formaté en markdown.",
            agent=self.writer_agent,
            async_execution=False,
            output_file="article.md"
        )

        self.edit_task = Task(
            description="Éditer l'article sur {topic} pour améliorer la clarté et la qualité.",
            expected_output="Article révisé, prêt pour la validation.",
            agent=self.editor_agent,
            async_execution=False,
            output_file="article_edited.md"
        )

        self.critique_task = Task(
            description="Évaluer l'article sur {topic} et fournir des retours pour validation.",
            expected_output="Commentaires détaillés sur l'article et suggestions d'amélioration.",
            agent=self.critic_agent,
            async_execution=False
        )

        # Création du crew avec un processus séquentiel
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
        # Initialiser le crew si ce n'est pas déjà fait
        if self.crew is None:
            self.on_startup()

        print("User Message:", user_message)
        # Lancer l'exécution de la pipeline avec le sujet fourni par l'utilisateur
        self.result = self.crew.kickoff(inputs={'topic': user_message})
        print("Fin de la pipeline.")
        print("Result:", self.result)
        # Retourner le résultat de la génération de l'article
        return self.result
