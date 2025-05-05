import asyncio
import logging
import uuid

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from a2a.server.agent_proxy import AgentProxy
from a2a.server.streaming_response_queue import StreamingResponseQueue
from a2a.server.task_store import InMemoryTaskStore, TaskStore
from a2a.types import (
    A2AError,
    CancelTaskRequest,
    CancelTaskResponse,
    CancelTaskSuccessResponse,
    GetTaskPushNotificationRequest,
    GetTaskPushNotificationResponse,
    GetTaskRequest,
    GetTaskResponse,
    GetTaskSuccessResponse,
    InternalError,
    JSONRPCError,
    JSONRPCErrorResponse,
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    SendTaskStreamingSuccessResponse,
    SendTaskSuccessResponse,
    SetTaskPushNotificationRequest,
    SetTaskPushNotificationResponse,
    Task,
    TaskIdParams,
    TaskNotFoundError,
    TaskQueryParams,
    TaskResubscriptionRequest,
    TaskSendParams,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    UnsupportedOperationError,
)
from a2a.utils import append_artifact_to_task


logger = logging.getLogger(__name__)


class A2ARequestHandler(ABC):
    """A2A request handler interface."""

    @abstractmethod
    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        pass

    @abstractmethod
    async def on_cancel_task(
        self, request: CancelTaskRequest
    ) -> CancelTaskResponse:
        pass

    @abstractmethod
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        pass

    @abstractmethod
    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncGenerator[SendTaskStreamingResponse, None]:
        yield SendTaskStreamingResponse(
            root=JSONRPCErrorResponse(
                id=request.id, error=UnsupportedOperationError()
            )
        )

    @abstractmethod
    async def on_set_task_push_notification(
        self, request: SetTaskPushNotificationRequest
    ) -> SetTaskPushNotificationResponse:
        pass

    @abstractmethod
    async def on_get_task_push_notification(
        self, request: GetTaskPushNotificationRequest
    ) -> GetTaskPushNotificationResponse:
        pass

    @abstractmethod
    async def on_resubscribe_to_task(
        self, request: TaskResubscriptionRequest
    ) -> AsyncGenerator[SendTaskStreamingResponse, None]:
        yield SendTaskStreamingResponse(
            root=JSONRPCErrorResponse(
                id=request.id, error=UnsupportedOperationError()
            )
        )


class DefaultA2ARequestHandler(A2ARequestHandler):
    """Default request handler for all incoming requests."""

    def __init__(
        self, agent_proxy: AgentProxy, task_store: TaskStore | None = None
    ) -> None:
        self.agent_proxy = agent_proxy
        self.task_store = task_store or InMemoryTaskStore()
        self.background_streaming_tasks: set[asyncio.Task[None]] = set()

    def _build_error_response(
        self, request_id: str | int | None, error: A2AError | JSONRPCError
    ) -> JSONRPCErrorResponse:
        """Helper method to build a JSONRPCErrorResponse."""
        return JSONRPCErrorResponse(
            id=request_id,
            error=error.root if isinstance(error, A2AError) else error,
        )

    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        """Default handler for 'tasks/get'."""
        task_query_params: TaskQueryParams = request.params
        task: Task | None = await self.task_store.get(task_query_params.id)
        if not task:
            return GetTaskResponse(
                root=self._build_error_response(
                    request.id, A2AError(root=TaskNotFoundError())
                )
            )
        return GetTaskResponse(
            root=GetTaskSuccessResponse(id=request.id, result=task)
        )

    async def on_cancel_task(
        self, request: CancelTaskRequest
    ) -> CancelTaskResponse:
        """Default handler for 'tasks/cancel'."""
        task_id_params: TaskIdParams = request.params
        task: Task | None = await self.task_store.get(task_id_params.id)
        if not task:
            return CancelTaskResponse(
                root=self._build_error_response(
                    request.id, A2AError(root=TaskNotFoundError())
                )
            )

        response: CancelTaskResponse = await self.agent_proxy.on_cancel(
            task, request
        )

        if isinstance(response.root, CancelTaskSuccessResponse):
            await self.task_store.save(response.root.result)

        return response

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """Default handler for 'tasks/send'."""
        task: Task = await self._get_task_obj(request.params)
        await self.task_store.save(task)

        response: SendTaskResponse = await self.agent_proxy.on_send(
            task, request
        )

        if isinstance(response.root, SendTaskSuccessResponse):
            task = response.root.result
            await self.task_store.save(task)

        return response

    async def on_send_task_subscribe(  # type: ignore
        self,
        request: SendTaskStreamingRequest,
    ) -> AsyncGenerator[SendTaskStreamingResponse, None]:
        """Default handler for 'tasks/sendSubscribe'."""
        task: Task = await self._get_task_obj(request.params)
        await self.task_store.save(task)

        return self._setup_sse_consumer(task, request)

    async def on_set_task_push_notification(
        self, request: SetTaskPushNotificationRequest
    ) -> SetTaskPushNotificationResponse:
        """Default handler for 'tasks/pushNotification/set'."""
        return SetTaskPushNotificationResponse(
            root=self._build_error_response(
                request.id, A2AError(root=UnsupportedOperationError())
            )
        )

    async def on_get_task_push_notification(
        self, request: GetTaskPushNotificationRequest
    ) -> GetTaskPushNotificationResponse:
        """Default handler for 'tasks/pushNotification/get'."""
        return GetTaskPushNotificationResponse(
            root=self._build_error_response(
                request.id, A2AError(root=UnsupportedOperationError())
            )
        )

    async def on_resubscribe_to_task(  # type: ignore
        self, request: TaskResubscriptionRequest
    ) -> AsyncGenerator[SendTaskStreamingResponse, None]:
        """Default handler for 'tasks/resubscribe'."""
        task_id_params: TaskIdParams = request.params
        task: Task | None = await self.task_store.get(task_id_params.id)

        return self._setup_sse_consumer(task, request)

    async def _setup_sse_consumer(
        self,
        task: Task | None,
        request: TaskResubscriptionRequest | SendTaskStreamingRequest,
    ) -> AsyncGenerator[SendTaskStreamingResponse, None]:
        # create a sse_queue that allows streaming responses back to the user
        sse_queue: StreamingResponseQueue = StreamingResponseQueue()

        # spawn a task for running the streaming agent
        streaming_task = asyncio.create_task(
            self._execute_streaming_agent_task(sse_queue, task, request)
        )
        # RUF006 - requires saving a reference to the asyncio.task to prevent GC
        self.background_streaming_tasks.add(streaming_task)
        streaming_task.add_done_callback(
            self.background_streaming_tasks.discard
        )

        while True:
            event: SendTaskStreamingResponse = await sse_queue.dequeue_event()
            yield event
            if isinstance(event.root, JSONRPCErrorResponse) or (
                isinstance(event.root.result, TaskStatusUpdateEvent)
                and event.root.result.final
            ):
                break

    async def _execute_streaming_agent_task(
        self,
        sse_queue: StreamingResponseQueue,
        task: Task | None,
        request: TaskResubscriptionRequest | SendTaskStreamingRequest,
    ) -> None:
        """Background task to run agent streaming."""
        try:
            # Note: 'task' may only be None here if the request was a resubscribe
            if not task:
                invalid_task_event = SendTaskStreamingResponse(
                    root=self._build_error_response(
                        request.id, A2AError(root=TaskNotFoundError())
                    )
                )
                sse_queue.enqueue_event(invalid_task_event)
                return

            if isinstance(request, TaskResubscriptionRequest):
                agent_response: AsyncGenerator[
                    SendTaskStreamingResponse, None
                ] = self.agent_proxy.on_resubscribe(task, request)  # type: ignore
            else:
                agent_response = self.agent_proxy.on_send_subscribe(  # type: ignore
                    task, request
                )

            async for response in agent_response:
                response_root = response.root
                if isinstance(response_root, SendTaskStreamingSuccessResponse):
                    if isinstance(response_root.result, TaskStatusUpdateEvent):
                        task.status = response_root.result.status
                        await self.task_store.save(task)
                    else:
                        append_artifact_to_task(task, response_root.result)
                        await self.task_store.save(task)
                sse_queue.enqueue_event(response)
        except Exception as e:
            logger.error(
                f'Error during streaming task execution for task {task.id if task else "unknown"}: {e}',
                exc_info=True,
            )
            # Ensure an error response is sent back if the stream fails unexpectedly
            error_response = SendTaskStreamingResponse(
                root=JSONRPCErrorResponse(
                    id=request.id,
                    error=InternalError(message=f'Streaming failed: {e}'),
                )
            )
            sse_queue.enqueue_event(error_response)

    async def _get_task_obj(self, task_send_params: TaskSendParams) -> Task:
        task: Task | None = await self.task_store.get(task_send_params.id)
        if not task_send_params.sessionId:
            task_send_params.sessionId = str(uuid.uuid4())
        if not task:
            session_id: str = task_send_params.sessionId
            return Task(
                id=task_send_params.id,
                sessionId=session_id,
                status=TaskStatus(state=TaskState.submitted),
                history=[task_send_params.message],
            )

        if task.history:
            task.history.append(task_send_params.message)
        else:
            task.history = [task_send_params.message]

        return task
