import os
import sys

import click
import httpx

from agent import CurrencyAgent  # type: ignore[import-untyped]
from agent_executor import CurrencyAgentExecutor  # type: ignore[import-untyped]
from dotenv import load_dotenv

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    DatabaseTaskStore,
    InMemoryPushNotifier,
    InMemoryTaskStore,
)
from a2a.types import AgentCapabilities, AgentCard, AgentSkill


# os is already imported

load_dotenv()


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=10000)
def main(host: str, port: int):
    if not os.getenv('GOOGLE_API_KEY'):
        print('GOOGLE_API_KEY environment variable not set.')
        sys.exit(1)

    client = httpx.AsyncClient()  # This is for the push_notifier

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
        agent_executor=CurrencyAgentExecutor(),
        task_store=task_store_instance,
        push_notifier=InMemoryPushNotifier(client),  # Preserving push_notifier
    )

    server = A2AStarletteApplication(
        agent_card=get_agent_card(host, port), http_handler=request_handler
    )
    import uvicorn

    uvicorn.run(server.build(), host=host, port=port)


def get_agent_card(host: str, port: int):
    """Returns the Agent Card for the Currency Agent."""
    capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
    skill = AgentSkill(
        id='convert_currency',
        name='Currency Exchange Rates Tool',
        description='Helps with exchange values between various currencies',
        tags=['currency conversion', 'currency exchange'],
        examples=['What is exchange rate between USD and GBP?'],
    )
    return AgentCard(
        name='Currency Agent',
        description='Helps with exchange rates for currencies',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        defaultInputModes=CurrencyAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=CurrencyAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )


if __name__ == '__main__':
    main()
