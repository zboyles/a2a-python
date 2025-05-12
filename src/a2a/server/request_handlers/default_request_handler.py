import asyncio
import functools
import logging
import threading

from collections.abc import AsyncGenerator

from a2a.server.agent_execution import AgentExecutor
from a2a.server.events import EventConsumer, EventQueue, Event
from a2a.server.request_handlers.request_handler import RequestHandler
from a2a.server.tasks import TaskManager, TaskStore, ResultAggregator
from a2a.server.agent_execution import RequestContext
from a2a.utils.errors import ServerError

from a2a.types import (
    Message,
    MessageSendParams,
    Task,
    TaskIdParams,
    TaskPushNotificationConfig,
    TaskQueryParams,
    UnsupportedOperationError,
    TaskNotFoundError
)


logger = logging.getLogger(__name__)


class DefaultRequestHandler(RequestHandler):
    """Default request handler for all incoming requests."""

    def __init__(
        self, agent_executor: AgentExecutor, task_store: TaskStore
    ) -> None:
        self.agent_executor = agent_executor
        self.task_store = task_store
        # This works for single binary solution. Needs a distributed approach for
        # true scalable deployment.
        self._task_queue: dict[str, EventQueue] = {}

    async def on_get_task(self, params: TaskQueryParams) -> Task | None:
        """Default handler for 'tasks/get'."""
        task: Task | None = await self.task_store.get(params.id)
        if not task:
            raise ServerError(error=TaskNotFoundError())
        return task

    async def on_cancel_task(self, params: TaskIdParams) -> Task | None:
        """Default handler for 'tasks/cancel'."""
        task: Task | None = await self.task_store.get(params.id)
        if not task:
            raise ServerError(error=TaskNotFoundError())

        task_manager = TaskManager(
            task_id=task.id,
            context_id=task.contextId,
            task_store=self.task_store,
            initial_message=None,
        )
        result_aggregator = ResultAggregator(task_manager)

        queue = EventQueue()
        await self.agent_executor.cancel(
            RequestContext(
                None,
                task_id=task.id,
                context_id=task.contextId,
                task=task,
            ),
            queue
        )
        consumer = EventConsumer(queue)
        return await result_aggregator.consume_all(consumer)

    async def _run_event_stream(self, request: RequestContext, queue: EventQueue):
        await self.agent_executor.execute(request, queue)
        queue.close()

    async def on_message_send(
        self, params: MessageSendParams
    ) -> Message | Task:
        """Default handler for 'message/send' interface"""
        task_manager = TaskManager(
            task_id=params.message.taskId,
            context_id=params.message.contextId,
            task_store=self.task_store,
            initial_message=params.message,
        )
        task: Task | None = await task_manager.get_task()
        if task:
            task = task_manager.update_with_message(params.message, task)
        result_aggregator = ResultAggregator(task_manager)
        # TODO to manage the non-blocking flows.
        queue = EventQueue()
        def _run_agent_stream() -> None:
            asyncio.run(
                self._run_event_stream(
                    RequestContext(
                        params,
                        task.id if task else None,
                        task.contextId if task else None,
                        task,
                    ),
                    queue,
                )
            )

        # If this is a follow up on an existing task, register the queue now
        task_id: str | None = task.id if task else None
        if task:
            self._task_queue[task_id] = queue

        thread = threading.Thread(target=_run_agent_stream)
        thread.start()
        consumer = EventConsumer(queue)
        # TODO - register the queue for the task upon the first sign it is a task.
        thread.join()
        return await result_aggregator.consume_all(consumer)


    async def on_message_send_stream(
        self, params: MessageSendParams
    ) -> AsyncGenerator[Event, None]:
        """Default handler for 'message/stream'."""
        task_manager = TaskManager(
            task_id=params.message.taskId,
            context_id=params.message.contextId,
            task_store=self.task_store,
            initial_message=params.message,
        )
        task: Task | None = await task_manager.get_task()

        if task:
            task = task_manager.update_with_message(params.message, task)

        result_aggregator = ResultAggregator(task_manager)
        queue = EventQueue()
        def _run_agent_stream() -> None:
            asyncio.run(
                self._run_event_stream(
                    RequestContext(
                        params,
                        task.id if task else None,
                        task.contextId if task else None,
                        task,
                    ),
                    queue,
                )
            )

        # If this is a follow up on an existing task, register the queue now
        task_id: str | None = task.id if task else None
        if task:
            self._task_queue[task_id] = queue

        thread = threading.Thread(target=_run_agent_stream)
        thread.start()

        consumer = EventConsumer(queue)
        async for event in result_aggregator.consume_and_emit(consumer):
            # Now we know we have a Task, register the queue
            if isinstance(event, Task) and event.id not in self._task_queue:
                self._task_queue[event.id] = queue
                task_id = event.id
            yield event

        thread.join()
        # Now clean up task queue registration
        if task_id in self._task_queue:
            del self._task_queue[task_id]

    async def on_set_task_push_notification_config(
        self, request: TaskPushNotificationConfig
    ) -> TaskPushNotificationConfig:
        """Default handler for 'tasks/pushNotificationConfig/set'."""
        raise UnsupportedOperationError()

    async def on_get_task_push_notification_config(
        self, request: TaskIdParams
    ) -> TaskPushNotificationConfig:
        """Default handler for 'tasks/pushNotificationConfig/get'."""
        raise UnsupportedOperationError()

    async def on_resubscribe_to_task(
        self, params: TaskIdParams
    ) -> AsyncGenerator[Event, None]:
        """Default handler for 'tasks/resubscribe'."""
        task: Task | None = await self.task_store.get(params.id)
        if not task:
            raise ServerError(error=TaskNotFoundError())
            return

        task_manager = TaskManager(
            task_id=task.id,
            context_id=task.contextId,
            task_store=self.task_store,
            initial_message=None,
        )

        result_aggregator = ResultAggregator(task_manager)

        # Need to tap the existing queue.
        if not task.id in self._task_queue:
            raise ServerError(error=TaskNotFoundError())
            return

        queue = self._task_queue[task.id].tap()
        consumer = EventConsumer(queue)
        async for event in result_aggregator.consume_and_emit(consumer):
            yield event
