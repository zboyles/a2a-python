import asyncio
import logging
import os

import click
import uvicorn

from adk_agent import create_agent  # type: ignore[import-not-found]
from adk_agent_executor import ADKAgentExecutor  # type: ignore[import-untyped]
from dotenv import load_dotenv
from google.adk.artifacts import (
    InMemoryArtifactService,  # type: ignore[import-untyped]
)
from google.adk.memory.in_memory_memory_service import (
    InMemoryMemoryService,  # type: ignore[import-untyped]
)
from google.adk.runners import Runner  # type: ignore[import-untyped]
from google.adk.sessions import (
    InMemorySessionService,  # type: ignore[import-untyped]
)
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import DatabaseTaskStore, InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill


# os is already imported

load_dotenv()

logging.basicConfig()


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=10007)
def main(host: str, port: int):
    # Verify an API key is set.
    # Not required if using Vertex AI APIs.
    if os.getenv('GOOGLE_GENAI_USE_VERTEXAI') != 'TRUE' and not os.getenv(
        'GOOGLE_API_KEY'
    ):
        raise ValueError(
            'GOOGLE_API_KEY environment variable not set and '
            'GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
        )

    skill = AgentSkill(
        id='check_availability',
        name='Check Availability',
        description="Checks a user's availability for a time using their Google Calendar",
        tags=['calendar'],
        examples=['Am I free from 10am to 11am tomorrow?'],
    )

    agent_card = AgentCard(
        name='Calendar Agent',
        description="An agent that can manage a user's calendar",
        url=f'http://{host}:{port}/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    adk_agent = asyncio.run(
        create_agent(
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        )
    )
    runner = Runner(
        app_name=agent_card.name,
        agent=adk_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    agent_executor = ADKAgentExecutor(runner, agent_card)

    async def handle_auth(request: Request) -> PlainTextResponse:
        await agent_executor.on_auth_callback(
            str(request.query_params.get('state')), str(request.url)
        )
        return PlainTextResponse('Authentication successful.')

    database_url = os.environ.get('DATABASE_URL')
    task_store_instance: InMemoryTaskStore | DatabaseTaskStore

    if database_url:
        print(f'Using DatabaseTaskStore with URL: {database_url} in {__file__}')
        task_store_instance = DatabaseTaskStore(
            db_url=database_url, create_table=True
        )
    else:
        print(f'DATABASE_URL not set in {__file__}, using InMemoryTaskStore.')
        task_store_instance = InMemoryTaskStore()

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor, task_store=task_store_instance
    )

    a2a_app = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
    routes = a2a_app.routes()
    routes.append(
        Route(
            path='/authenticate',
            methods=['GET'],
            endpoint=handle_auth,
        )
    )
    app = Starlette(routes=routes)

    uvicorn.run(app, host=host, port=port)


if __name__ == '__main__':
    main()
