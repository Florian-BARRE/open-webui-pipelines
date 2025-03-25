import logging
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel, Field
from schemas import OpenAIChatMessage

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class Pipeline:
    class Valves(BaseModel):
        """Configurable parameters for the pipeline."""
        VAR_EXAMPLE: str = Field(default="DEFAULT_VALUE", description="An example environment variable")

    def __init__(self):
        """Initialize the pipeline."""
        self.name = "Pipeline Example"
        self.valves = self.Valves()

    async def on_startup(self):
        """Function called when the server starts."""
        logger.info(f"Starting up pipeline: {self.name}")

    async def on_shutdown(self):
        """Function called when the server shuts down."""
        logger.info(f"Shutting down pipeline: {self.name}")

    async def on_valves_updated(self):
        """Function called when the valves are updated."""
        logger.debug("Valves update detected.")

    async def inlet(self, body: dict, user: dict) -> dict:
        """Function called before making the OpenAI API request."""
        logger.debug(f"Inlet of pipeline: {self.name}")
        logger.debug(f"Request body: {body}")
        logger.debug(f"User: {user}")
        return body

    async def outlet(self, body: dict, user: dict) -> dict:
        """Function called after receiving the OpenAI API response."""
        logger.debug(f"Outlet of pipeline: {self.name}")
        logger.debug(f"Response body: {body}")
        logger.debug(f"User: {user}")
        return body

    async def pipe(
            self, user_message: str, model_id: str, messages: List[dict], body: dict,
            __event_emitter__=None, __user__=None, __metadata__=None, __files__=None
    ) -> Union[str, Generator, Iterator]:
        """Main function of the pipeline to process messages."""
        logger.debug(f"pipe called for pipeline: {self.name}")
        logger.debug(f"user_message: {user_message}")
        logger.debug(f"model_id: {model_id}")
        logger.debug(f"messages: {messages}")
        logger.debug(f"body: {body}")
        logger.debug(f"__event_emitter__: {__event_emitter__}")
        logger.debug(f"__user__: {__user__}")
        logger.debug(f"__metadata__: {__metadata__}")
        logger.debug(f"__files__: {__files__}")

        logger.info(f"Processing user message: {user_message}")
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Processing in progress...", "done": False}
                }
            )
        if __files__:
            for file in __files__:
                logger.info(f"Received file: {file['filename']}")
        if body.get("title", False):
            logger.info("Title generation request detected.")
        response = f"Response from pipeline '{self.name}' to: {user_message}"
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Processing completed.", "done": True}
                }
            )
        return response
