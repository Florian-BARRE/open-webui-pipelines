"""
title: Dummy Pipeline for Debugging
author: Florian Barre
author_url: https://github.com/Florian-BARRE
git_url: https://github.com/Florian-BARRE/open-webui-pipelines
description: Dummy pipeline for debugging purposes.
required_open_webui_version: 0.4.3
version: 0.1.0
license: GPL-3.0
"""

import os
from logging import getLogger
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel, Field

# Set up logging
logger = getLogger(__name__)
logger.setLevel("DEBUG")


class Pipeline:
    class Valves(BaseModel):
        A_ENV_VAR: str = Field(default="A_DEFAULT_VALUE", description="An environment variable")

    def __init__(self):
        self.name = "Dummy Pipeline"

        # Initialize valve parameters
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )

        logger.debug("Valves: %s", self.valves)

    async def on_startup(self):
        # This function is called when the server is started.
        logger.debug("on_startup")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        logger.debug("on_shutdown")
        pass

    def pipe(
            self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        logger.debug("pipe")

        # print all input parameters
        logger.debug(f"user_message: {user_message}")
        logger.debug(f"model_id: {model_id}")
        logger.debug(f"messages: {messages}")
        logger.debug(f"body: {body}")

        return "Dummy response"
