from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from a2a.types import (
    CancelTaskRequest,
    CancelTaskResponse,
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    Task,
    TaskResubscriptionRequest,
)


class AgentProxy(ABC):
    """Agent Proxy interface."""

    @abstractmethod
    async def on_send(
        self, task: Task, request: SendTaskRequest
    ) -> SendTaskResponse:
        pass

    @abstractmethod
    async def on_send_subscribe(
        self, task: Task, request: SendTaskStreamingRequest
    ) -> AsyncGenerator[SendTaskStreamingResponse, None]:
        pass

    @abstractmethod
    async def on_cancel(
        self, task: Task, request: CancelTaskRequest
    ) -> CancelTaskResponse:
        pass

    @abstractmethod
    async def on_resubscribe(
        self, task: Task, request: TaskResubscriptionRequest
    ) -> AsyncGenerator[SendTaskStreamingResponse, None]:
        pass
