from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from a2a.types import (
    CancelTaskRequest,
    CancelTaskSuccessResponse,
    JSONRPCErrorResponse,
    SendTaskRequest,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    SendTaskSuccessResponse,
    Task,
    TaskResubscriptionRequest,
)


class AgentProxy(ABC):
    """Agent Proxy interface."""

    @abstractmethod
    async def on_send(
        self, task: Task, request: SendTaskRequest
    ) -> SendTaskSuccessResponse | JSONRPCErrorResponse:
        pass

    @abstractmethod
    async def on_send_subscribe(
        self, task: Task, request: SendTaskStreamingRequest
    ) -> AsyncGenerator[SendTaskStreamingResponse, None]:
        pass

    @abstractmethod
    async def on_cancel(
        self, task: Task, request: CancelTaskRequest
    ) -> CancelTaskSuccessResponse | JSONRPCErrorResponse:
        pass

    @abstractmethod
    async def on_resubscribe(
        self, task: Task, request: TaskResubscriptionRequest
    ) -> AsyncGenerator[SendTaskStreamingResponse, None]:
        pass
