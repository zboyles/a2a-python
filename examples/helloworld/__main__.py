from agent_executor import (
    HelloWorldAgentExecutor,  # type: ignore[import-untyped]
)

import os

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, DatabaseTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill


if __name__ == '__main__':
    skill = AgentSkill(
        id='hello_world',
        name='Returns hello world',
        description='just returns hello world',
        tags=['hello world'],
        examples=['hi', 'hello world'],
    )

    agent_card = AgentCard(
        name='Hello World Agent',
        description='Just a hello world agent',
        url='http://localhost:9999/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    database_url = os.environ.get("DATABASE_URL")
    task_store_instance: InMemoryTaskStore | DatabaseTaskStore

    if database_url:
        print(f"Using DatabaseTaskStore with URL: {database_url}")
        # For this example, we assume create_table=True is desired for the DatabaseTaskStore.
        # In a production scenario, schema management might be handled separately (e.g., migrations).
        task_store_instance = DatabaseTaskStore(db_url=database_url, create_table=True)
        # Note: DatabaseTaskStore.initialize() is async and should ideally be called
        # during async app startup (e.g., Starlette's on_startup).
        # Here, we rely on its internal _ensure_initialized() called by its methods.
    else:
        print("DATABASE_URL not set, using InMemoryTaskStore.")
        task_store_instance = InMemoryTaskStore()

    request_handler = DefaultRequestHandler(
        agent_executor=HelloWorldAgentExecutor(),
        task_store=task_store_instance,
    )

    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
    import uvicorn

    uvicorn.run(server.build(), host='0.0.0.0', port=9999)
